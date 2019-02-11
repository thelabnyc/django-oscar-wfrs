class WellsFargoException(Exception):
    pass


class TransactionDenied(WellsFargoException):
    status = None


class CreditApplicationDenied(WellsFargoException):
    pass


class CreditApplicationPending(WellsFargoException):
    inquiry = None
