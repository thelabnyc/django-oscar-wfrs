from django.utils.translation import ugettext_lazy as _


CREDIT_APP_APPROVED = 'E0'
CREDIT_APP_DECISION_DELAYED = 'E1'
CREDIT_APP_FORMAT_ERROR = 'E2'
CREDIT_APP_WFF_ERROR = 'E3'
CREDIT_APP_DENIED = 'E4'

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

INQUIRY_SUCCESS = 'I0'
INQUIRY_ACCT_NOT_FOUND = 'I1'
INQUIRY_SYS_ERROR = 'I2'
OTB_SUCCESS = 'H0'
OTB_FAILED = 'H1'
OTB_NO_MATCH = 'H2'
OTB_ACCT_NOT_FOUND = 'H3'
OTB_DENIED = 'H4'
OTB_OTHER = 'H5'
INQUIRY_STATUSES = (
    (INQUIRY_SUCCESS, _("Account Inquiry Succeeded")),
    (INQUIRY_ACCT_NOT_FOUND, _("Could Not Find Requested Account")),
    (INQUIRY_SYS_ERROR, _("Wells Fargo System Error")),
    (OTB_SUCCESS, _("OTB Success")),
    (OTB_FAILED, _("OTB Failed")),
    (OTB_NO_MATCH, _("OTB No Match")),
    (OTB_ACCT_NOT_FOUND, _("OTB Account Not Found")),
    (OTB_DENIED, _("OTB Denied")),
    (OTB_OTHER, _("OTB External Status Code")),
)


TRANS_TYPE_AUTH = '5'
TRANS_TYPE_CANCEL_AUTH = '7'
# TRANS_TYPE_CHARGE = '3' # TODO: handle charges
# TRANS_TYPE_AUTH_AND_CHARGE = '1'
# TRANS_TYPE_AUTH_AND_CHARGE_TIMEOUT_REVERSAL = '2'
TRANS_TYPE_RETURN_CREDIT = '4'
TRANS_TYPE_RETURN_CREDIT_TIMEOUT_REVERSAL = '9'
TRANS_TYPE_VOID_SALE = 'VS'
TRANS_TYPE_VOID_RETURN = 'VR'
TRANS_TYPE_INQUIRY = '8'
TRANS_TYPE_APPLY = 'A6'
TRANS_TYPES = (
    (TRANS_TYPE_AUTH, _('Authorization for Future Charge')),
    (TRANS_TYPE_CANCEL_AUTH, _('Cancel Existing Authorization')),
    # (TRANS_TYPE_CHARGE, _('Charge for Previous Authorization')), # TODO: handle charges
    # (TRANS_TYPE_AUTH_AND_CHARGE, _('Authorize and Charge')),
    # (TRANS_TYPE_AUTH_AND_CHARGE_TIMEOUT_REVERSAL, _('Time-out Reversal for Previous "Authorization and Charge"')),
    (TRANS_TYPE_RETURN_CREDIT, _('Return or Credit')),
    (TRANS_TYPE_RETURN_CREDIT_TIMEOUT_REVERSAL, _('Time-out Reversal for Return or Credit')),
    (TRANS_TYPE_VOID_SALE, _('Void Sale')),
    (TRANS_TYPE_VOID_RETURN, _('Void Return')),
    # These transaction types are special and are handled separately
    # (TRANS_TYPE_INQUIRY, _('Account Inquiry')),
    # (TRANS_TYPE_APPLY, _('Credit Line Application')),
)


INDIVIDUAL, JOINT = ('I', 'J')
APP_TYPES = (
    (INDIVIDUAL, _('Individual')),
    (JOINT, _('Joint')),
)


ENGLISH, FRENCH = ('E', 'F')
LANGUAGES = (
    (ENGLISH, _('English')),
    (FRENCH, _('French')),
)


US, CA = ('US', 'CA')
REGIONS = (
    (US, _('United States')),
    (CA, _('Canada')),
)


EN_US, EN_CA, FR_CA = ('en_US', 'en_CA', 'fr_CA')
LOCALE_CHOICES = (
    (EN_US, _('English (US)')),
    (EN_CA, _('English (CA)')),
    (FR_CA, _('French (CA)')),
)
PREQUAL_LOCALE_CHOICES = (
    (EN_US, _('English (US)')),
)
LOCALES = {
    US: {
        ENGLISH: EN_US,
    },
    CA: {
        ENGLISH: EN_CA,
        FRENCH: FR_CA,
    },
}


HOUSING_STATUSES = {
    US: (
        ('R', _('Rent')),
        ('O', _('Own')),
        ('OT', _('Other')),
    ),
    CA: (
        ('R', _('Rent')),
        ('O', _('Own')),
    ),
}


PHOTO_ID_TYPES = {
    CA: (
        ('OA', _('Old Age Security Card')),
        ('DL', _('Driver’s License')),
        ('PI', _('Provincial ID')),
        ('PA', _('Canadian Passport')),
        ('CN', _('Certificate of Citizenship or Naturalization')),
        ('IS', _('Certificate of Indian Status')),
        ('CC', _('Canadian Citizen Form 1000 or 1442')),
    ),
}


APPLICATION_FORM_EXCLUDE_FIELDS = ('user', 'submitting_user', 'last4_account_number', 'inquiries', 'credentials')


ENTRY_POINT_WEB = 'web'
ENTRY_POINT_POS = 'pos'
ENTRY_POINT_CHOICES = (
    (ENTRY_POINT_WEB, 'Web'),
    (ENTRY_POINT_POS, 'Point of Sale'),
)

PREQUAL_TRANS_STATUS_APPROVED = 'A'  # Instant pre-screen approved
PREQUAL_TRANS_STATUS_REJECTED = 'D'  # Instant pre-screen not approved
PREQUAL_TRANS_STATUS_ERROR = 'E'  # System Error
PREQUAL_TRANS_STATUS_DOWN = 'M'  # Down for Maintenance
PREQUAL_TRANS_STATUS_CHOICES = (
    (PREQUAL_TRANS_STATUS_APPROVED, _('Pre-screen Approved')),
    (PREQUAL_TRANS_STATUS_REJECTED, _('Pre-screen Not Approved')),
    (PREQUAL_TRANS_STATUS_ERROR, _('System Error')),
    (PREQUAL_TRANS_STATUS_DOWN, _('Down for Maintenance')),
)

PREQUAL_CUSTOMER_RESP_NONE = ''  # No response from customer
PREQUAL_CUSTOMER_RESP_CLOSE = 'CLOSE'  # Customer closed offer
PREQUAL_CUSTOMER_RESP_ACCEPT = 'YES'  # Customer accepted offer
PREQUAL_CUSTOMER_RESP_REJECT = 'NO'  # Customer rejected offer
PREQUAL_CUSTOMER_RESP_SDKPRESENTED = 'SDKPRESENTED'  # WFRS SDK Presented Pre-Approval Offer
PREQUAL_CUSTOMER_RESP_CHOICES = (
    (PREQUAL_CUSTOMER_RESP_NONE, _('')),
    (PREQUAL_CUSTOMER_RESP_CLOSE, _('Offer Closed')),
    (PREQUAL_CUSTOMER_RESP_ACCEPT, _('Offer Accepted')),
    (PREQUAL_CUSTOMER_RESP_REJECT, _('Offer Rejected')),
    (PREQUAL_CUSTOMER_RESP_SDKPRESENTED, _('Offer Presented By PLCCA SDK')),
)

PREQUAL_REDIRECT_APP_APPROVED = '41'
