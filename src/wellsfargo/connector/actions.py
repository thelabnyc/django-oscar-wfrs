from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from ..core.constants import (
    TRANS_TYPE_INQUIRY,
)
from ..models import (
    APICredentials,
    AccountInquiryResult,
)
from ..settings import (
    WFRS_INQUIRY_WSDL,
    WFRS_OTB_WSDL,
)
import soap
import uuid
import re
import logging

logger = logging.getLogger(__name__)


def submit_inquiry(account_number, current_user=None, locale='en_US'):
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
    result.available_credit = _as_decimal(resp.openToBuy)

    result.last_payment_date = _as_date(resp.lastPaymentDate)
    result.last_payment_amount = _as_decimal(resp.lastPayment)

    result.payment_due_date = _as_date(resp.lastPaymentDate)
    result.payment_due_amount = _as_decimal(resp.paymentDue)

    result.save()
    return result


# def check_pre_qualification_status(prequal_request, return_url=None, current_user=None):
#     client = soap.get_client(WFRS_PRE_QUAL_WSDL, 'WFRS')
#     type_name = _find_namespaced_name(client, 'WFRS_InstantPreScreenRequest')
#     data = client.factory.create(type_name)

#     data.localeString = prequal_request.locale
#     data.uuid = prequal_request.uuid
#     data.behaviorVersion = "1"

#     creds = APICredentials.get_credentials(current_user)
#     data.userName = creds.username
#     data.servicePassword = creds.password
#     data.merchantNumber = creds.merchant_num

#     data.transactionCode = 'P1'
#     data.entryPoint = prequal_request.entry_point
#     if return_url:
#         data.returnUrl = return_url

#     data.firstName = prequal_request.first_name
#     data.lastName = prequal_request.last_name
#     data.address1 = prequal_request.line1
#     data.city = prequal_request.city
#     data.state = prequal_request.state
#     data.postalCode = prequal_request.postcode
#     data.phone = _format_phone(prequal_request.phone)

#     # Save the credentials used to make the request
#     prequal_request.merchant_name = creds.name
#     prequal_request.merchant_num = creds.merchant_num
#     prequal_request.credentials = creds
#     prequal_request.save()

#     # Submit the pre-qualification request
#     resp = client.service.instantPreScreen(data)

#     # Check for faults
#     if resp.faults and resp.faults.item:
#         for fault in resp.faults.item:
#             logger.info(fault.faultDetailString)
#             raise ValidationError(fault.faultDetailString)

#     # Sanity check the response
#     if resp.transactionStatus is None or resp.uniqueId is None:
#         logger.info('WFRS pre-qualification request return null data for pre-request[{}]'.format(prequal_request.pk))
#         return None

#     # Save the pre-qualification response data
#     response = PreQualificationResponse()
#     response.request = prequal_request
#     response.status = resp.transactionStatus
#     response.message = resp.message or ''
#     response.offer_indicator = resp.offerIndicator or ''
#     response.credit_limit = _as_decimal(resp.upToLimit)
#     response.response_id = resp.uniqueId
#     response.application_url = urllib.parse.unquote(resp.url or '')
#     response.customer_response = PREQUAL_CUSTOMER_RESP_NONE
#     response.save()
#     return response


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
    result.available_credit = _as_decimal(resp.availableCredit)

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
