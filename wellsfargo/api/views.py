from rest_framework.response import Response
from rest_framework.reverse import reverse_lazy
from rest_framework import (
    authentication,
    permissions,
    mixins,
    viewsets,
    generics,
)
from oscar.core.loading import get_model
from oscarapi.views.checkout import CheckoutView as OscarCheckoutView
from ..core.constants import (
    US, CA,
    INDIVIDUAL, JOINT
)
from .serializers import (
    CheckoutSerializer,
    AppSelectionSerializer,
    USCreditAppSerializer,
    USJointCreditAppSerializer,
    CACreditAppSerializer,
    CAJointCreditAppSerializer,
    AccountSerializer,
)
from .permissions import IsAccountOwner, add_session_account
from ..core import exceptions as core_exceptions
from . import exceptions as api_exceptions

Account = get_model('oscar_accounts', 'Account')


class CheckoutView(OscarCheckoutView):
    """
    Checkout and use a WFRS account as payment.

    POST(basket, shipping_address, wfrs_source_account,
         [total, shipping_method_code, shipping_charge, billing_address]):
    {
        "basket": "/api/baskets/1/",
        "wfrs_source_account": "/api/wfrs/accounts/42/",
        "guest_email": "foo@example.com",
        "total": "100.0",
        "shipping_charge": {
            "currency": "EUR",
            "excl_tax": "10.0",
            "tax": "0.6"
        },
        "shipping_method_code": "no-shipping-required",
        "shipping_address": {
            "country": "/api/countries/NL/",
            "first_name": "Henk",
            "last_name": "Van den Heuvel",
            "line1": "Roemerlaan 44",
            "line2": "",
            "line3": "",
            "line4": "Kroekingen",
            "notes": "Niet STUK MAKEN OK!!!!",
            "phone_number": "+31 26 370 4887",
            "postcode": "7777KK",
            "state": "Gerendrecht",
            "title": "Mr"
        }
    }

    Returns the order object.
    """
    serializer_class = CheckoutSerializer

    def post(self, *args, **kwargs):
        resp = super().post(*args, **kwargs)
        # Work around bug where DRF think the order we're returning is a basket, checks basket.can_be_edited, and fails because it's an order.
        self.permission_classes = []
        return resp



class SelectCreditAppView(generics.GenericAPIView):
    serializer_class = AppSelectionSerializer

    def post(self, request):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            'url': self._get_app_url(request, **serializer.validated_data),
        })

    def _get_app_url(self, request, region, app_type):
        routes = {
            US: {
                INDIVIDUAL: reverse_lazy('wfrs-api-apply-us-individual', request=request),
                JOINT: reverse_lazy('wfrs-api-apply-us-join', request=request),
            },
            CA: {
                INDIVIDUAL: reverse_lazy('wfrs-api-apply-ca-individual', request=request),
                JOINT: reverse_lazy('wfrs-api-apply-ca-joint', request=request),
            },
        }
        return routes.get(region, {}).get(app_type)



class BaseCreditAppView(generics.GenericAPIView):
    def post(self, request):
        serializer = self.get_serializer_class()(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            account = serializer.save()
        except core_exceptions.CreditApplicationDenied as e:
            raise api_exceptions.CreditApplicationDenied()

        add_session_account(request, account)
        serializer = AccountSerializer(account, context={'request': request})
        return Response(serializer.data)



class USCreditAppView(BaseCreditAppView):
    serializer_class = USCreditAppSerializer



class USJointCreditAppView(BaseCreditAppView):
    serializer_class = USJointCreditAppSerializer



class CACreditAppView(BaseCreditAppView):
    serializer_class = CACreditAppSerializer



class CAJointCreditAppView(BaseCreditAppView):
    serializer_class = CAJointCreditAppSerializer



class AccountView(viewsets.ModelViewSet):
    permission_classes = (IsAccountOwner, )
    model = Account
    serializer_class = AccountSerializer

    def get_queryset(self):
        ids = IsAccountOwner.list_valid_account_ids(self.request)
        return Account.objects.filter(id__in=ids).order_by('id').all()
