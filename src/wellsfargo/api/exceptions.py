from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework import status


class CreditApplicationPending(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "pending"
    default_detail = _("Credit Application approval is pending")
    inquiry = None


class CreditApplicationDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "denied"
    default_detail = _("Credit Application was denied by Wells Fargo")
