from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.db import transaction
from oscar_accounts import facade
import soap
import uuid
import re
import logging

from ..core.constants import CREDIT_APP_APPROVED, TRANS_APPROVED, TRANS_TYPE_INQUIRY, TRANS_TYPE_APPLY
from ..core.exceptions import TransactionDenied, CreditApplicationDenied
from ..core.structures import CreditApplicationResult, AccountInquiryResult
from ..models import APICredentials, TransferMetadata, FinancingPlan
from ..settings import (
    WFRS_TRANSACTION_WSDL,
    WFRS_INQUIRY_WSDL,
    WFRS_CREDIT_APP_WSDL
)

logger = logging.getLogger(__name__)


def submit_transaction(trans_request, current_user=None):
    client = soap.get_client(WFRS_TRANSACTION_WSDL, 'WFRS')

    trans_request.source_account.primary_user = trans_request.user
    trans_request.source_account.save()
    if not trans_request.source_account.can_be_authorised_by(trans_request.user):
        raise TransactionDenied('%s can not authorize transfer from %s' % (trans_request.user, trans_request.source_account))

    creds = APICredentials.get_credentials(current_user)

    request = client.factory.create('ns2:Transaction')
    request.userName = creds.username
    request.setupPassword = creds.password
    request.merchantNumber = creds.merchant_num
    request.uuid = uuid.uuid1()
    request.transactionCode = trans_request.type_code
    request.localeString = trans_request.source_account.wfrs_metadata.locale
    request.accountNumber = trans_request.source_account.wfrs_metadata.account_number
    request.planNumber = trans_request.financing_plan.plan_number
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
    with transaction.atomic():
        transfer = facade.transfer(
            source=trans_request.source_account,
            destination=trans_request.dest_account,
            amount=_as_decimal(resp.amount),
            user=trans_request.user,
            merchant_reference=resp.uuid)
        TransferMetadata.objects.create(
            transfer=transfer,
            type_code=resp.transactionCode,
            ticket_number=resp.ticketNumber,
            financing_plan=FinancingPlan.objects.filter(plan_number=resp.planNumber).first(),
            auth_number=resp.authorizationNumber,
            status=resp.transactionStatus,
            message=resp.transactionMessage,
            disclosure=resp.disclosure)
        trans_request.transfer = transfer
        trans_request.save()
    return transfer


def submit_inquiry(account, current_user=None):
    client = soap.get_client(WFRS_INQUIRY_WSDL, 'WFRS')

    creds = APICredentials.get_credentials(current_user)

    request = client.factory.create('ns2:Inquiry')
    request.userName = creds.username
    request.setupPassword = creds.password
    request.merchantNumber = creds.merchant_num
    request.uuid = uuid.uuid1()
    request.transactionCode = TRANS_TYPE_INQUIRY
    request.localeString = account.wfrs_metadata.locale
    request.accountNumber = account.wfrs_metadata.account_number

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
    result.account = account
    result.balance = _as_decimal(resp.accountBalance)
    result.open_to_buy = _as_decimal(resp.openToBuy)
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

    # Check for approval
    if resp.transactionStatus != CREDIT_APP_APPROVED:
        raise CreditApplicationDenied(resp.transactionStatus)

    # Build response
    result = CreditApplicationResult()
    result.application = app
    result.transaction_status = resp.transactionStatus
    result.account_number = resp.wfAccountNumber
    result.credit_limit = _as_decimal(resp.creditLimit)
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
