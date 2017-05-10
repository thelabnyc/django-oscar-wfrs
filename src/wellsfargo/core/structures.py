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
