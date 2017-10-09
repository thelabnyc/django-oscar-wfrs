from django.core.exceptions import ImproperlyConfigured
from ..settings import WFRS_FRAUD_PROTECTION
import importlib


def screen_transaction(request, order):
    klass = WFRS_FRAUD_PROTECTION['fraud_protection']
    kwargs = WFRS_FRAUD_PROTECTION.get('fraud_protection_kwargs', {})
    return _get_fraud_screener(klass, kwargs).screen_transaction(request, order)


def _get_fraud_screener(klass, kwargs):
    FraudScreener = _load_cls_from_abs_path(klass)
    screener = FraudScreener(**kwargs)
    return screener


def _load_cls_from_abs_path(path):
    pkgname, fnname = path.rsplit('.', 1)
    try:
        pkg = importlib.import_module(pkgname)
        return getattr(pkg, fnname)
    except (ImportError, AttributeError):
        raise ImproperlyConfigured('Could not import class at path {}'.format(path))
