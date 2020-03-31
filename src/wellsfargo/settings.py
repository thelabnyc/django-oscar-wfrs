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


# WFRS Gateway API Company ID
WFRS_GATEWAY_COMPANY_ID = overridable('WFRS_GATEWAY_COMPANY_ID', '')

# WFRS Gateway API Entity ID
WFRS_GATEWAY_ENTITY_ID = overridable('WFRS_GATEWAY_ENTITY_ID', '')

# Hostname to use when connecting to the WFRS Gateway API
WFRS_GATEWAY_API_HOST = overridable('WFRS_GATEWAY_API_HOST', 'api-sandbox.wellsfargo.com')

# Consumer Key used when generating API keys for the WFRS Gateway API
WFRS_GATEWAY_CONSUMER_KEY = overridable('WFRS_GATEWAY_CONSUMER_KEY', '')

# Consumer Secret used when generating API keys for the WFRS Gateway API
WFRS_GATEWAY_CONSUMER_SECRET = overridable('WFRS_GATEWAY_CONSUMER_SECRET', '')

# File path to the TLS client cert used for WFRS Gateway API authentication
WFRS_GATEWAY_CLIENT_CERT_PATH = overridable('WFRS_GATEWAY_CLIENT_CERT_PATH', None)

# File path to the private key for the TLS client cert (corresponding to WFRS_GATEWAY_CLIENT_CERT_PATH)
WFRS_GATEWAY_PRIV_KEY_PATH = overridable('WFRS_GATEWAY_PRIV_KEY_PATH', None)

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
