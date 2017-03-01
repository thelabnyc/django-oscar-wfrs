from decimal import Decimal
from .constants import EN_US, TRANS_TYPE_AUTH


class TransactionRequest(object):
    locale = EN_US
    type_code = TRANS_TYPE_AUTH
    auth_number = '000000'
    user = None
    account_number = None
    plan_number = None
    amount = Decimal('0.00')
    ticket_number = None


class AccountInquiryResult(object):
    transaction_status = ""
    account_number = None
    credit_limit = Decimal('0.00')
    balance = Decimal('0.00')
    open_to_buy = Decimal('0.00')


class CreditApplicationResult(object):
    application = None
    transaction_status = ""
    account_number = ""
    credit_limit = Decimal('0.00')
    balance = Decimal('0.00')
    open_to_buy = Decimal('0.00')
