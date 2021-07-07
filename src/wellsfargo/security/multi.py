from . import _get_encryptor
import logging

logger = logging.getLogger(__name__)


class MultiEncryption(object):
    """
    Combine multiple encryption classes together to make it possible to rotate
    keys, or to change from one method of encryption to another, without breaking
    old data or needing downtime for re-encryption.

    Usage:

    WFRS_SECURITY = {
        'encryptor': 'wellsfargo.security.multi.MultiEncryption',
        'encryptor_kwargs': {
            'encryptors': [
                {
                    'encryptor': 'wellsfargo.security.fernet.FernetEncryption',
                    'encryptor_kwargs': {
                        'key': b'mbgOpeXTyhhy1DgXreVOt6QMNu2Eem0RmPvJLCndpIw=',
                    },
                },
                {
                    'encryptor': 'wellsfargo.security.fernet.FernetEncryption',
                    'encryptor_kwargs': {
                        'key': b'U3Nyi57e55H2weKVmEPzrGdv18b0bGt3e542rg1J1N8=',
                    },
                },
            ],
        },
    }

    All new data will be encrypted using the first encryption method supplied in the
    ``encryptors`` keyword-argument. When decrypting data, each method in the ``encryptors``
    will be attempted (in-order) until one successfully decrypts the data or until the
    list is exhausted.
    """

    def __init__(self, encryptors):
        self.encryptors = encryptors

    def encrypt(self, value):
        """Accept a string and return binary data"""
        klass = self.encryptors[0]["encryptor"]
        kwargs = self.encryptors[0].get("encryptor_kwargs", {})
        return _get_encryptor(klass, kwargs).encrypt(value)

    def decrypt(self, blob):
        """Accept binary data and return a string"""
        for encryptor in self.encryptors:
            klass = encryptor["encryptor"]
            kwargs = encryptor.get("encryptor_kwargs", {})
            value = _get_encryptor(klass, kwargs).decrypt(blob)
            if value is not None:
                return value
        return None
