from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from ..core.constants import (
    CREDIT_APP_APPROVED,
    CREDIT_APP_DECISION_DELAYED,
    CREDIT_APP_FORMAT_ERROR,
    CREDIT_APP_WFF_ERROR,
    TRANS_APPROVED,
    TRANS_TYPE_INQUIRY,
    TRANS_TYPE_APPLY,
    EN_US,
)
from ..core.exceptions import TransactionDenied, CreditApplicationPending, CreditApplicationDenied
from ..core.structures import CreditApplicationResult, AccountInquiryResult
from ..models import APICredentials, TransferMetadata, FinancingPlan
from ..settings import (
    WFRS_TRANSACTION_WSDL,
    WFRS_INQUIRY_WSDL,
    WFRS_CREDIT_APP_WSDL
)
import soap
import uuid
import re
import logging

logger = logging.getLogger(__name__)


def submit_transaction(trans_request, current_user=None):
    client = soap.get_client(WFRS_TRANSACTION_WSDL, 'WFRS')

    request = client.factory.create('ns2:Transaction')
    request.uuid = uuid.uuid1()

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

    # Check for faults
    if resp.faults:
        for fault in resp.faults:
            logger.info(fault.faultDetailString)
            raise ValidationError(fault.faultDetailString)

    # Check for approval
    if resp.transactionStatus != TRANS_APPROVED:
        raise TransactionDenied('%s: %s' % (resp.transactionStatus, resp.transactionMessage))

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
    transfer.disclosure = resp.disclosure
    transfer.save()
    return transfer


def submit_inquiry(account_number, current_user=None, locale=EN_US):
    client = soap.get_client(WFRS_INQUIRY_WSDL, 'WFRS')

    request = client.factory.create('ns2:Inquiry')
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
    result.transaction_status = resp.transactionStatus
    result.account_number = resp.wfAccountNumber
    result.balance = _as_decimal(resp.accountBalance)
    result.open_to_buy = _as_decimal(resp.openToBuy)
    result.credit_limit = _as_decimal(resp.accountBalance + resp.openToBuy)
    return result


def submit_credit_application(app, current_user=None):
    client = soap.get_client(WFRS_CREDIT_APP_WSDL, 'WFRS')
    data = client.factory.create('ns2:CreditApp')

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

    # Check if application approval is pending
    if resp.transactionStatus == CREDIT_APP_DECISION_DELAYED:
        raise CreditApplicationPending('Credit Application is approval is pending.')

    # Check for approval
    if resp.transactionStatus != CREDIT_APP_APPROVED:
        raise CreditApplicationDenied('Credit Application was denied by Wells Fargo.')

    # Credit application must be approved. Build response
    result = CreditApplicationResult()
    result.application = app
    result.transaction_status = resp.transactionStatus
    result.account_number = resp.wfAccountNumber
    result.credit_limit = _as_decimal(resp.creditLimit)
    result.balance = Decimal('0.00')
    result.open_to_buy = result.credit_limit
    return result


def _format_date(date):
    return date.strftime('%m/%d/%Y') if date else None


def _format_phone(number):
    return re.sub(r'[^0-9]+', '', number) if number else None


def _format_ssn(number):
    return re.sub(r'[^0-9]+', '', number) if number else None


def _as_decimal(string):
    try:
        return Decimal(string).quantize(Decimal('.01'))
    except (TypeError, InvalidOperation):
        return Decimal('0.00')
