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


WFRS_TRANSACTION_WSDL = overridable('WFRS_TRANSACTION_WSDL', 'https://retailservices-uat.wellsfargo.com/services/SubmitTransactionService?WSDL')
WFRS_INQUIRY_WSDL = overridable('WFRS_INQUIRY_WSDL', 'https://retailservices-uat.wellsfargo.com/services/SubmitInquiryService?WSDL')
WFRS_CREDIT_APP_WSDL = overridable('WFRS_CREDIT_APP_WSDL', 'https://retailservices-uat.wellsfargo.com/services/SubmitCreditAppService?WSDL')

WFRS_ACCOUNT_TYPE = overridable('WFRS_ACCOUNT_TYPE', 'Credit Line (Wells Fargo)')

WFRS_INITIAL_ORDER_STATUS = overridable('WFRS_INITIAL_ORDER_STATUS', 'new')
WFRS_PAYMENT_SOURCE = overridable('WFRS_PAYMENT_SOURCE', 'Credit Line (Wells Fargo)')
WFRS_TRANSACTION_STATUS = 'Complete'
