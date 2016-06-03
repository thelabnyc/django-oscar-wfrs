class WellsFargoException(Exception):
    pass


class TransactionDenied(WellsFargoException):
    pass


class CreditApplicationDenied(WellsFargoException):
    pass
