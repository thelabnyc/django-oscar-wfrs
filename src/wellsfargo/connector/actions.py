from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from ..core.constants import (
    CREDIT_APP_APPROVED,
    CREDIT_APP_DECISION_DELAYED,
    CREDIT_APP_FORMAT_ERROR,
    CREDIT_APP_WFF_ERROR,
    INQUIRY_SUCCESS,
    TRANS_APPROVED,
    TRANS_TYPE_INQUIRY,
    TRANS_TYPE_APPLY,
    EN_US,
    PREQUAL_CUSTOMER_RESP_NONE,
    OTB_SUCCESS,
)
from ..core.exceptions import TransactionDenied, CreditApplicationPending, CreditApplicationDenied
from ..models import APICredentials, TransferMetadata, AccountInquiryResult, FinancingPlan, PreQualificationResponse
from ..settings import (
    WFRS_TRANSACTION_WSDL,
    WFRS_INQUIRY_WSDL,
    WFRS_CREDIT_APP_WSDL,
    WFRS_PRE_QUAL_WSDL,
    WFRS_OTB_WSDL,
)
import urllib.parse
import soap
import uuid
import re
import logging

logger = logging.getLogger(__name__)


def submit_transaction(trans_request, current_user=None, transaction_uuid=None, persist=True):
    client = soap.get_client(WFRS_TRANSACTION_WSDL, 'WFRS')
    type_name = _find_namespaced_name(client, 'Transaction')
    request = client.factory.create(type_name)

    # If a uuid was given, use that instead of generating a new one. This allows tracing fraud responses through to transactions.
    request.uuid = transaction_uuid if transaction_uuid else uuid.uuid1()

    creds = APICredentials.get_credentials(current_user)
    request.userName = creds.username
    request.setupPassword = creds.password
    request.merchantNumber = creds.merchant_num

    request.transactionCode = trans_request.type_code
    request.localeString = trans_request.locale
    request.accountNumber = trans_request.account_number
    request.planNumber = trans_request.plan_number
    request.amount = _as_decimal(trans_request.amount)
    request.authorizationNumber = trans_request.auth_number
    request.ticketNumber = trans_request.ticket_number

    # Submit
    resp = client.service.submitTransaction(request)

    # Persist transaction data and WF specific metadata
    transfer = TransferMetadata()
    transfer.user = trans_request.user
    transfer.credentials = creds
    transfer.account_number = resp.accountNumber
    transfer.merchant_reference = resp.uuid
    transfer.amount = _as_decimal(resp.amount)
    transfer.type_code = resp.transactionCode
    transfer.ticket_number = resp.ticketNumber
    transfer.financing_plan = FinancingPlan.objects.filter(plan_number=resp.planNumber).first()
    transfer.auth_number = resp.authorizationNumber
    transfer.status = resp.transactionStatus
    transfer.message = resp.transactionMessage
    transfer.disclosure = resp.disclosure or ''
    if persist:
        transfer.save()

    # Check for faults
    if resp.faults:
        for fault in resp.faults:
            logger.info(fault.faultDetailString)
            raise ValidationError(fault.faultDetailString)

    # Check for approval
    if resp.transactionStatus != TRANS_APPROVED:
        exc = TransactionDenied('%s: %s' % (resp.transactionStatus, resp.transactionMessage))
        exc.status = resp.transactionStatus
        raise exc

    return transfer


def submit_inquiry(account_number, current_user=None, locale=EN_US):
    client = soap.get_client(WFRS_INQUIRY_WSDL, 'WFRS')
    type_name = _find_namespaced_name(client, 'Inquiry')
    request = client.factory.create(type_name)
    request.uuid = uuid.uuid1()
    request.transactionCode = TRANS_TYPE_INQUIRY

    creds = APICredentials.get_credentials(current_user)
    request.userName = creds.username
    request.setupPassword = creds.password
    request.merchantNumber = creds.merchant_num

    request.localeString = locale
    request.accountNumber = account_number

    # Submit
    resp = client.service.submitInquiry(request)

    # Check for faults
    if resp.faults:
        for fault in resp.faults:
            logger.info(fault.faultDetailString)
            raise ValidationError(fault.faultDetailString)

    # Check for errors
    error_msg = resp.sorErrorDescription.strip() if resp.sorErrorDescription else None
    if error_msg:
        raise ValidationError(error_msg)

    # Build response
    result = AccountInquiryResult()

    result.status = resp.transactionStatus

    result.account_number = resp.wfAccountNumber

    result.first_name = resp.firstName or ''
    result.middle_initial = resp.middleInitial or ''
    result.last_name = resp.lastName or ''

    # This is kind of awful, but WFRS only uses national phone number (with an implied +1 country code). So, we
    # add back the country code to make it valid to store in the DB.
    # E.g. Take "5559998888" and convert it to "+15559998888"
    result.phone_number = '+1{}'.format(resp.phone)

    result.address = resp.address or ''

    result.credit_limit = (_as_decimal(resp.accountBalance) + _as_decimal(resp.openToBuy))
    result.balance = _as_decimal(resp.accountBalance)
    result.open_to_buy = _as_decimal(resp.openToBuy)

    result.last_payment_date = _as_date(resp.lastPaymentDate)
    result.last_payment_amount = _as_decimal(resp.lastPayment)

    result.payment_due_date = _as_date(resp.lastPaymentDate)
    result.payment_due_amount = _as_decimal(resp.paymentDue)

    result.save()
    return result


def submit_credit_application(app, current_user=None):
    client = soap.get_client(WFRS_CREDIT_APP_WSDL, 'WFRS')
    type_name = _find_namespaced_name(client, 'CreditApp')
    data = client.factory.create(type_name)

    creds = APICredentials.get_credentials(current_user)
    data.userName = creds.username
    data.setupPassword = creds.password
    data.merchantNumber = creds.merchant_num

    data.uuid = uuid.uuid1()
    data.transactionCode = TRANS_TYPE_APPLY
    data.checkStatus = '0'

    data.localeString = app.locale
    data.languagePreference = app.language

    data.purchasePrice = app.purchase_price
    data.optionalInsurance = '1' if app.insurance else '0'
    data.salesPerson = app.sales_person_id
    data.newSalesPerson = app.new_sales_person
    data.emailAddress = app.email

    data.mainFirstName = app.main_first_name
    data.mainLastName = app.main_last_name
    data.mainMiddleInitial = app.main_middle_initial
    data.mainDOB = _format_date(app.main_date_of_birth)
    data.mainSSN = _format_ssn(app.main_ssn)
    data.mainAddress1 = app.main_address_line1
    data.mainAddress2 = app.main_address_line2
    data.mainCity = app.main_address_city
    data.mainStateOrProvince = app.main_address_state
    data.mainPostalCode = app.main_address_postcode
    data.mainHomePhone = _format_phone(app.main_home_phone)
    data.mainTimeAtAddress = app.main_time_at_address
    data.mainHousingStatus = app.main_housing_status
    data.mainHomeValue = app.main_home_value
    data.mainMortgageBalance = app.main_mortgage_balance
    data.mainEmployerName = app.main_employer_name
    data.mainTimeAtEmployer = app.main_time_at_employer
    data.mainEmployerPhone = _format_phone(app.main_employer_phone)
    data.mainAnnualIncome = app.main_annual_income
    data.mainCellPhone = _format_phone(app.main_cell_phone)
    data.mainOccupation = app.main_occupation
    data.mainPhotoIdType = getattr(app, 'main_photo_id_type', None)
    data.mainPhotoIdNumber = getattr(app, 'main_photo_id_number', None)
    data.mainDLStateOrProvince = getattr(app, 'main_drivers_license_province', None)
    data.mainPhotoIdExpDate = _format_date( getattr(app, 'main_photo_id_expiration', None) )

    data.individualJointIndicator = 'J' if app.is_joint else 'I'
    if app.is_joint:
        data.jointFirstName = app.joint_first_name
        data.jointLastName = app.joint_last_name
        data.jointMiddleInitial = app.joint_middle_initial
        data.jointDOB = _format_date(app.joint_date_of_birth)
        data.jointSSN = _format_ssn(app.joint_ssn)
        data.jointAddress1 = app.joint_address_line1
        data.jointAddress2 = app.joint_address_line2
        data.jointCity = app.joint_address_city
        data.jointStateOrProvince = app.joint_address_state
        data.jointPostalCode = app.joint_address_postcode
        data.jointEmployerName = app.joint_employer_name
        data.jointTimeAtEmployer = app.joint_time_at_employer
        data.jointEmployerPhone = _format_phone(app.joint_employer_phone)
        data.jointAnnualIncome = app.joint_annual_income
        data.jointCellPhone = _format_phone(app.joint_cell_phone)
        data.jointOccupation = app.joint_occupation
        data.jointPhotoIdType = getattr(app, 'joint_photo_id_type', None)
        data.jointPhotoIdNumber = getattr(app, 'joint_photo_id_number', None)
        data.jointDLStateOrProvince = getattr(app, 'joint_drivers_license_province', None)
        data.jointPhotoIdExpDate = _format_date( getattr(app, 'joint_photo_id_expiration', None) )

    # Submit
    resp = client.service.submitCreditApp(data)

    # Save the status and credentials used to apply
    app.status = resp.transactionStatus or ''
    app.credentials = creds
    app.save()

    # Check for faults
    if resp.faults:
        for fault in resp.faults:
            logger.info(fault.faultDetailString)
            raise ValidationError(fault.faultDetailString)

    # Check for errors
    error_msg = resp.sorErrorDescription.strip() if resp.sorErrorDescription else None
    if error_msg:
        logger.info(error_msg)
        raise ValidationError(error_msg)

    # Check for any other errors we didn't catch already for any reason
    if resp.transactionStatus in (CREDIT_APP_FORMAT_ERROR, CREDIT_APP_WFF_ERROR):
        raise ValidationError('An unknown error occurred.')

    # If the status is not either Approved or Pending, it must be denied
    if resp.transactionStatus not in (CREDIT_APP_APPROVED, CREDIT_APP_DECISION_DELAYED):
        raise CreditApplicationDenied('Credit Application was denied by Wells Fargo.')

    # Save the suffix of the account number
    app.account_number = resp.wfAccountNumber
    app.save()

    # Record an account inquiry
    result = AccountInquiryResult()
    result.credit_app_source = app
    result.status = INQUIRY_SUCCESS
    result.account_number = resp.wfAccountNumber
    result.first_name = app.main_first_name
    result.middle_initial = app.main_middle_initial
    result.last_name = app.main_last_name
    result.phone_number = '+1{}'.format(data.mainHomePhone)
    result.address = app.main_address_line1
    result.credit_limit = _as_decimal(resp.creditLimit)
    result.balance = Decimal('0.00')
    result.open_to_buy = result.credit_limit
    result.save()

    # Check if application approval is pending
    if resp.transactionStatus == CREDIT_APP_DECISION_DELAYED:
        pending = CreditApplicationPending('Credit Application is approval is pending.')
        pending.inquiry = result
        raise pending

    return result


def check_pre_qualification_status(prequal_request, return_url=None, current_user=None):
    client = soap.get_client(WFRS_PRE_QUAL_WSDL, 'WFRS')
    type_name = _find_namespaced_name(client, 'WFRS_InstantPreScreenRequest')
    data = client.factory.create(type_name)

    data.localeString = prequal_request.locale
    data.uuid = prequal_request.uuid
    data.behaviorVersion = "1"

    creds = APICredentials.get_credentials(current_user)
    data.userName = creds.username
    data.servicePassword = creds.password
    data.merchantNumber = creds.merchant_num

    data.transactionCode = 'P1'
    data.entryPoint = prequal_request.entry_point
    if return_url:
        data.returnUrl = return_url

    data.firstName = prequal_request.first_name
    data.lastName = prequal_request.last_name
    data.address1 = prequal_request.line1
    data.city = prequal_request.city
    data.state = prequal_request.state
    data.postalCode = prequal_request.postcode
    data.phone = _format_phone(prequal_request.phone)

    # Save the credentials used to make the request
    prequal_request.credentials = creds
    prequal_request.save()

    # Submit the pre-qualification request
    resp = client.service.instantPreScreen(data)

    # Check for faults
    if resp.faults and resp.faults.item:
        for fault in resp.faults.item:
            logger.info(fault.faultDetailString)
            raise ValidationError(fault.faultDetailString)

    # Sanity check the response
    if resp.transactionStatus is None or resp.uniqueId is None:
        logger.info('WFRS pre-qualification request return null data for pre-request[{}]'.format(prequal_request.pk))
        return None

    # Save the pre-qualification response data
    response = PreQualificationResponse()
    response.request = prequal_request
    response.status = resp.transactionStatus
    response.message = resp.message or ''
    response.offer_indicator = resp.offerIndicator or ''
    response.credit_limit = _as_decimal(resp.upToLimit)
    response.response_id = resp.uniqueId
    response.application_url = urllib.parse.unquote(resp.url or '')
    response.customer_response = PREQUAL_CUSTOMER_RESP_NONE
    response.save()
    return response


def check_pre_qualification_account_status(prequal_response):
    client = soap.get_client(WFRS_OTB_WSDL, 'WFRS')
    type_name = _find_namespaced_name(client, 'WFRS_OTBRequest')
    data = client.factory.create(type_name)

    data.localeString = prequal_response.request.locale
    data.uuid = uuid.uuid1()
    data.behaviorVersion = "1"

    data.userName = prequal_response.request.credentials.username
    data.servicePassword = prequal_response.request.credentials.password
    data.merchantNumber = prequal_response.request.credentials.merchant_num

    data.transactionCode = 'C1'

    data.uniqueId = prequal_response.response_id
    data.firstName = prequal_response.request.first_name
    data.lastName = prequal_response.request.last_name

    # Submit the pre-qualification request
    resp = client.service.submitOTB(data)

    # Check for faults
    if resp.faults and resp.faults.item:
        for fault in resp.faults.item:
            logger.info(fault.faultDetailString)
            raise ValidationError(fault.faultDetailString)

    # If the returned status isn't successful, theres nothing else to do.
    if resp.transactionStatus != OTB_SUCCESS:
        logger.info('Received OTB Response with unsuccessful transaction status. Status: {}. Message: {}'.format(
            resp.transactionStatus, resp.message))
        return None

    # If no account number was returned, theres nothing else to do.
    if not resp.accountNumber:
        logger.info('Received OTB Response without account number. Status: {}. Message: {}'.format(
            resp.transactionStatus, resp.message))
        return None

    # Build response
    result = AccountInquiryResult()
    result.prequal_response_source = prequal_response
    result.status = resp.transactionStatus

    result.account_number = resp.accountNumber

    result.first_name = prequal_response.request.first_name
    result.middle_initial = ""
    result.last_name = prequal_response.request.last_name
    result.phone_number = prequal_response.request.phone
    result.address = resp.mainAddress1 or prequal_response.request.line1

    result.credit_limit = _as_decimal(resp.creditLimit)
    result.balance = (_as_decimal(resp.creditLimit) - _as_decimal(resp.availableCredit))
    result.open_to_buy = _as_decimal(resp.availableCredit)

    result.save()
    logger.info('Saved OTB Response as AccountInquiryResult[{}]. Status: {}. Message: {}'.format(
        result.pk, result.status, resp.message))
    return result


def _format_date(date):
    return date.strftime('%m/%d/%Y') if date else None


def _format_phone(number):
    if number:
        return number.national_number
    return None


def _format_ssn(number):
    return re.sub(r'[^0-9]+', '', number) if number else None


def _as_date(string, fstring='%m%d%y'):
    try:
        return datetime.strptime(string, fstring)
    except ValueError:
        return None


def _as_decimal(string):
    try:
        return Decimal(string).quantize(Decimal('.01'))
    except (TypeError, InvalidOperation):
        return Decimal('0.00')


def _find_namespaced_name(client, bare_name):
    for stype in client.sd[0].types:
        namespaced_name = client.sd[0].xlate(stype[0])
        if ':' in namespaced_name:
            prefix, bare = namespaced_name.split(':', 1)
            if bare == bare_name:
                return namespaced_name
    return bare_name
