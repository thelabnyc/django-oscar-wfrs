from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def overridable(name, default=None, required=False, cast=None):
    if required:
        if not hasattr(settings, name) or not getattr(settings, name):
            raise ImproperlyConfigured("%s must be defined in Django settings" % name)
    value = getattr(settings, name, default)
    if cast:
        value = cast(value)
    return value


# SOAP service for sending transaction requests to WFRS
WFRS_TRANSACTION_WSDL = overridable('WFRS_TRANSACTION_WSDL', 'https://retailservices-uat.wellsfargo.com/services/SubmitTransactionService?WSDL')

# SOAP service for obtaining account status information from WFRS
WFRS_INQUIRY_WSDL = overridable('WFRS_INQUIRY_WSDL', 'https://retailservices-uat.wellsfargo.com/services/SubmitInquiryService?WSDL')

# SOAP service for applying for a new Wells Fargo account
WFRS_CREDIT_APP_WSDL = overridable('WFRS_CREDIT_APP_WSDL', 'https://retailservices-uat.wellsfargo.com/services/SubmitCreditAppService?WSDL')

# SOAP service for checking account pre-qualification status
WFRS_PRE_QUAL_WSDL = overridable('WFRS_PRE_QUAL_WSDL', 'https://retailservices-uat.wellsfargo.com/services/WFRS_InstantPreScreenService?WSDL')

# SOAP service for checking account pre-qualification application status (the status of an account after the user was pre-qualified)
WFRS_OTB_WSDL = overridable('WFRS_OTB_WSDL', 'https://retailservices-uat.wellsfargo.com/services/WFRS_SubmitOTBService?WSDL')


# Encryption settings (used to protect account numbers stored in the database)
WFRS_SECURITY = {
    'encryptor': 'wellsfargo.security.fernet.FernetEncryption',
    'encryptor_kwargs': {},
}
WFRS_SECURITY.update( overridable('WFRS_SECURITY', {}) )

# If using the defaults, make sure an encryption key is configured
if WFRS_SECURITY['encryptor'] == 'wellsfargo.security.fernet.FernetEncryption':
    if WFRS_SECURITY['encryptor_kwargs'].get('key') is None:
        raise ImproperlyConfigured((
            "You must supply a value for WFRS_SECURITY['encryptor_kwargs']['key'] in settings. "
            "See https://cryptography.io/en/latest/fernet/ for details."
        ))


# Fraud Protection Settings
WFRS_FRAUD_PROTECTION = {
    'fraud_protection': 'wellsfargo.fraud.dummy.DummyFraudProtection',
    'fraud_protection_kwargs': {},
}
WFRS_FRAUD_PROTECTION.update( overridable('WFRS_FRAUD_PROTECTION', {}) )

WFRS_MAX_TRANSACTION_ATTEMPTS = overridable('WFRS_MAX_TRANSACTION_ATTEMPTS', 2)
