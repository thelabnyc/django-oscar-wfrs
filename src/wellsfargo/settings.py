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


# Wells Fargo API WSDLs
WFRS_TRANSACTION_WSDL = overridable('WFRS_TRANSACTION_WSDL', 'https://retailservices-uat.wellsfargo.com/services/SubmitTransactionService?WSDL')
WFRS_INQUIRY_WSDL = overridable('WFRS_INQUIRY_WSDL', 'https://retailservices-uat.wellsfargo.com/services/SubmitInquiryService?WSDL')
WFRS_CREDIT_APP_WSDL = overridable('WFRS_CREDIT_APP_WSDL', 'https://retailservices-uat.wellsfargo.com/services/SubmitCreditAppService?WSDL')


# Encryption settings (used to protect account numbers stored in the database)
WFRS_SECURITY = {
    'encryptor': 'wellsfargo.security.fernet.FernetEncryption',
    'encryptor_kwargs': {},
}
WFRS_SECURITY.update( overridable('WFRS_SECURITY', {}) )

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
