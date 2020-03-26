from django.core.exceptions import ImproperlyConfigured
from ..settings import WFRS_SECURITY
import importlib
import pickle
import base64


def encrypt_account_number(account_number):
    """Accepts account number as a string and returns cipher-text bytes"""
    return _get_configured_encryptor().encrypt(account_number)


def decrypt_account_number(encrypted):
    """Accepts cipher-text bytes and return account number as a string"""
    return _get_configured_encryptor().decrypt(encrypted)


def encrypt_pickle(obj):
    """Accepts object, pickles it, encrypts it, and returns the cipher-text bytes"""
    pickled_bytes = pickle.dumps(obj)
    encoded_str = base64.b64encode(pickled_bytes).decode()
    return _get_configured_encryptor().encrypt(encoded_str)


def decrypt_pickle(encrypted):
    """Accepts cipher-text bytes, decrypts it, unpickles it, and returns the object"""
    encoded_str = _get_configured_encryptor().decrypt(encrypted)
    pickled_bytes = base64.b64decode(encoded_str)
    return pickle.loads(pickled_bytes)


def _get_configured_encryptor():
    klass = WFRS_SECURITY['encryptor']
    kwargs = WFRS_SECURITY.get('encryptor_kwargs', {})
    return _get_encryptor(klass, kwargs)


def _get_encryptor(klass, kwargs):
    Encryptor = _load_cls_from_abs_path(klass)
    encryptor = Encryptor(**kwargs)
    return encryptor


def _load_cls_from_abs_path(path):
    pkgname, fnname = path.rsplit('.', 1)
    try:
        pkg = importlib.import_module(pkgname)
        return getattr(pkg, fnname)
    except (ImportError, AttributeError):
        raise ImproperlyConfigured('Could not import class at path {}'.format(path))
