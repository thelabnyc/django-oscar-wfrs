from ..settings import WFRS_SECURITY
import importlib


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
