from django.core.exceptions import ImproperlyConfigured
from ..settings import WFRS_SECURITY
import importlib


def encrypt_account_number(account_number):
    klass = WFRS_SECURITY['encryptor']
    kwargs = WFRS_SECURITY.get('encryptor_kwargs', {})
    return _get_encryptor(klass, kwargs).encrypt(account_number)


def decrypt_account_number(encrypted):
    klass = WFRS_SECURITY['encryptor']
    kwargs = WFRS_SECURITY.get('encryptor_kwargs', {})
    return _get_encryptor(klass, kwargs).decrypt(encrypted)


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
