from django.utils.translation import ugettext_lazy as _


CREDIT_APP_TRANS_CODE_DEVICE_NON_CONSUMER = 'A2'
CREDIT_APP_TRANS_CODE_DEVICE_CONSUMER = 'AH'
CREDIT_APP_TRANS_CODE_CREDIT_APPLICATION = 'A6'
CREDIT_APP_TRANS_CODE_MERCHANT_HOSTED_ONLINE = 'MAH'
CREDIT_APP_TRANS_CODE_MERCHANT_HOSTED_IN_STORE = 'MIS'
CREDIT_APP_TRANS_CODE_ = 'B1'
CREDIT_APP_TRANS_CODE_B2 = 'B2'
CREDIT_APP_TRANS_CODE_B3 = 'B3'
CREDIT_APP_TRANS_CODE_B4 = 'B4'
CREDIT_APP_TRANS_CODES = (
    (CREDIT_APP_TRANS_CODE_DEVICE_NON_CONSUMER, _("Applications from a non-consumer device")),
    (CREDIT_APP_TRANS_CODE_DEVICE_CONSUMER, _("Applications from a consumer's device")),
    (CREDIT_APP_TRANS_CODE_CREDIT_APPLICATION, _("Credit application")),
    (CREDIT_APP_TRANS_CODE_MERCHANT_HOSTED_ONLINE, _("Merchant hosted at home, online")),
    (CREDIT_APP_TRANS_CODE_MERCHANT_HOSTED_IN_STORE, _("Merchant hosted in store")),
    (CREDIT_APP_TRANS_CODE_, _("Batch integrated at home")),
    (CREDIT_APP_TRANS_CODE_B2, _("Batch get customer data")),
    (CREDIT_APP_TRANS_CODE_B3, _("Batch merchant hosted in store")),
    (CREDIT_APP_TRANS_CODE_B4, _("Batch merchant hosted at home")),
)

HOUSING_STATUS_RENT = 'Rent'
HOUSING_STATUS_OWN = 'Own'
HOUSING_STATUS_OTHER = 'Other'
HOUSING_STATUSES = (
    (HOUSING_STATUS_RENT, _('Rent')),
    (HOUSING_STATUS_OWN, _('Own')),
    (HOUSING_STATUS_OTHER, _('Other')),
)

ENGLISH, SPANISH = ('E', 'S')
LANGUAGES = (
    (ENGLISH, _('English')),
    (SPANISH, _('Spanish')),
)

CREDIT_APP_APPROVED = 'APPROVED'
CREDIT_APP_PENDING = 'PENDING'
CREDIT_APP_DENIED = 'DENIED'
CREDIT_APP_STATUSES = (
    ('', _("Unknown")),
    (CREDIT_APP_APPROVED, _("Approved")),
    (CREDIT_APP_PENDING, _("Pending")),
    (CREDIT_APP_DENIED, _("Denied")),
)

TRANS_DECLINED = 'A0'
TRANS_APPROVED = 'A1'
TRANS_VOID_NO_MATCH_FOUND = 'A2'
TRANS_VOID_MATCH_DUPLICATE = 'A3'
TRANS_STATUSES = (
    (TRANS_DECLINED, _("Transaction not approved or declined. For time-out reversal and void transactions, match was found but was already funded.")),
    (TRANS_APPROVED, _("Approved. For time-out reversal and void transactions, match was found and processed.")),
    (TRANS_VOID_NO_MATCH_FOUND, _("Time-out reversal or void approved, but no matching transaction was found.")),
    (TRANS_VOID_MATCH_DUPLICATE, _("Time-out reversal or void approved, but matched duplicate transactions.")),
)

TRANS_TYPE_AUTH = '5'
TRANS_TYPE_CANCEL_AUTH = '7'
TRANS_TYPE_CHARGE = '3'
TRANS_TYPE_AUTH_AND_CHARGE = '1'
TRANS_TYPE_AUTH_AND_CHARGE_TIMEOUT_REVERSAL = '2'
TRANS_TYPE_RETURN_CREDIT = '4'
TRANS_TYPE_RETURN_CREDIT_TIMEOUT_REVERSAL = '9'
TRANS_TYPE_VOID_SALE = 'VS'
TRANS_TYPE_VOID_RETURN = 'VR'
TRANS_TYPE_INQUIRY = '8'
TRANS_TYPE_APPLY = 'A6'
TRANS_TYPES = (
    (TRANS_TYPE_AUTH, _('Authorization for Future Charge')),
    (TRANS_TYPE_CANCEL_AUTH, _('Cancel Existing Authorization')),
    (TRANS_TYPE_CHARGE, _('Charge for Previous Authorization')),
    (TRANS_TYPE_AUTH_AND_CHARGE, _('Authorize and Charge')),
    (TRANS_TYPE_AUTH_AND_CHARGE_TIMEOUT_REVERSAL, _('Time-out Reversal for Previous "Authorization and Charge"')),
    (TRANS_TYPE_RETURN_CREDIT, _('Return or Credit')),
    (TRANS_TYPE_RETURN_CREDIT_TIMEOUT_REVERSAL, _('Time-out Reversal for Return or Credit')),
    (TRANS_TYPE_VOID_SALE, _('Void Sale')),
    (TRANS_TYPE_VOID_RETURN, _('Void Return')),
    # These transaction types are special and are handled separately
    # (TRANS_TYPE_INQUIRY, _('Account Inquiry')),
    # (TRANS_TYPE_APPLY, _('Credit Line Application')),
)

ENTRY_POINT_WEB = 'WEB'
ENTRY_POINT_POS = 'POS'
ENTRY_POINT_CHOICES = (
    (ENTRY_POINT_WEB, _('Web')),
    (ENTRY_POINT_POS, _('Point of Sale')),
)

PREQUAL_TRANS_STATUS_APPROVED = 'A'  # Instant pre-screen approved
PREQUAL_TRANS_STATUS_REJECTED = 'D'  # Instant pre-screen not approved
PREQUAL_TRANS_STATUS_ERROR = 'E'  # System Error
PREQUAL_TRANS_STATUS_DOWN = 'M'  # Down for Maintenance

_trans_qual_names = {
    PREQUAL_TRANS_STATUS_APPROVED: _('Pre-qualification Approved'),
    PREQUAL_TRANS_STATUS_REJECTED: _('Pre-qualification Not Approved'),
    PREQUAL_TRANS_STATUS_ERROR: _('System Error'),
    PREQUAL_TRANS_STATUS_DOWN: _('Down for Maintenance'),
}
_trans_screen_names = {
    PREQUAL_TRANS_STATUS_APPROVED: _('Pre-screen Approved'),
    PREQUAL_TRANS_STATUS_REJECTED: _('Pre-screen Not Approved'),
    PREQUAL_TRANS_STATUS_ERROR: _('System Error'),
    PREQUAL_TRANS_STATUS_DOWN: _('Down for Maintenance'),
}


def get_prequal_trans_status_name(status_code, customer_initiated=True):
    if customer_initiated:
        return _trans_qual_names.get(status_code, PREQUAL_TRANS_STATUS_REJECTED)
    return _trans_screen_names.get(status_code, PREQUAL_TRANS_STATUS_REJECTED)


PREQUAL_TRANS_STATUS_CHOICES = (
    (PREQUAL_TRANS_STATUS_APPROVED, get_prequal_trans_status_name(PREQUAL_TRANS_STATUS_APPROVED)),
    (PREQUAL_TRANS_STATUS_REJECTED, get_prequal_trans_status_name(PREQUAL_TRANS_STATUS_REJECTED)),
    (PREQUAL_TRANS_STATUS_ERROR, get_prequal_trans_status_name(PREQUAL_TRANS_STATUS_ERROR)),
    (PREQUAL_TRANS_STATUS_DOWN, get_prequal_trans_status_name(PREQUAL_TRANS_STATUS_DOWN)),
)

PREQUAL_CUSTOMER_RESP_NONE = ''  # No response from customer
PREQUAL_CUSTOMER_RESP_CLOSE = 'CLOSE'  # Customer closed offer
PREQUAL_CUSTOMER_RESP_ACCEPT = 'YES'  # Customer accepted offer
PREQUAL_CUSTOMER_RESP_REJECT = 'NO'  # Customer rejected offer
PREQUAL_CUSTOMER_RESP_SDKPRESENTED = 'SDKPRESENTED'  # WFRS SDK Presented Pre-Approval Offer
PREQUAL_CUSTOMER_RESP_CHOICES = (
    (PREQUAL_CUSTOMER_RESP_NONE, ''),
    (PREQUAL_CUSTOMER_RESP_CLOSE, _('Offer Closed')),
    (PREQUAL_CUSTOMER_RESP_ACCEPT, _('Offer Accepted')),
    (PREQUAL_CUSTOMER_RESP_REJECT, _('Offer Rejected')),
    (PREQUAL_CUSTOMER_RESP_SDKPRESENTED, _('Offer Presented By PLCCA SDK')),
)

PREQUAL_REDIRECT_APP_APPROVED = '41'
