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
