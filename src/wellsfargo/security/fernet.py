from cryptography.fernet import Fernet, InvalidToken
from django.utils.encoding import force_bytes, force_text
import logging

logger = logging.getLogger(__name__)


class FernetEncryption(object):
    """
    Encrypt data using `Python Fernet <https://cryptography.io/en/latest/fernet/>`_.

    Usage:

    WFRS_SECURITY = {
        'encryptor': 'wellsfargo.security.fernet.FernetEncryption',
        'encryptor_kwargs': {
            'key': b'U3Nyi57e55H2weKVmEPzrGdv18b0bGt3e542rg1J1N8=',
        },
    }

    The given key should be a URL-safe base64-encoded 32-byte encryption key and should obviously
    not be hard-coded in the application.
    """
    def __init__(self, key):
        self.fernet = Fernet(key=key)

    def encrypt(self, value):
        """Accept a string and return binary data"""
        value = force_bytes(value)
        return self.fernet.encrypt(value)

    def decrypt(self, blob):
        """Accept binary data and return a string"""
        blob = force_bytes(blob)
        try:
            value = self.fernet.decrypt(blob)
        except InvalidToken:
            logger.warning('Unable to decrypt account number blob.')
            return None
        return force_text(value)
