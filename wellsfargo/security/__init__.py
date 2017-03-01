from cryptography.fernet import Fernet, InvalidToken
from django.utils.encoding import force_bytes, force_text
from ..settings import WFRS_SECURITY
import importlib
import logging

logger = logging.getLogger(__name__)


class FernetEncryption(object):
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
        except InvalidToken as e:
            logger.exception('Unable to decrypt account number blob.')
            return None
        return force_text(value)


def encrypt_account_number(account_number):
    return _get_encryptor().encrypt(account_number)


def decrypt_account_number(encrypted):
    return _get_encryptor().decrypt(encrypted)


def _get_encryptor():
    Encryptor = _load_cls_from_abs_path(WFRS_SECURITY['encryptor'])
    kwargs = WFRS_SECURITY.get('encryptor_kwargs', {})
    encryptor = Encryptor(**kwargs)
    return encryptor


def _load_cls_from_abs_path(path):
    pkgname, fnname = path.rsplit('.', 1)
    pkg = importlib.import_module(pkgname)
    return getattr(pkg, fnname)
