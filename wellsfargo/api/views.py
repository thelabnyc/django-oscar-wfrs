from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse_lazy
from rest_framework import (
    views,
    viewsets,
    generics,
)
from oscar.core.loading import get_model
from oscarapi.basket import operations
from ..core.constants import (
    US, CA,
    INDIVIDUAL, JOINT
)
from .serializers import (
    AppSelectionSerializer,
    USCreditAppSerializer,
    USJointCreditAppSerializer,
    CACreditAppSerializer,
    CAJointCreditAppSerializer,
    AccountSerializer,
    FinancingPlanSerializer,
)
from .permissions import IsAccountOwner
from ..core import exceptions as core_exceptions
from ..utils import list_plans_for_basket
from . import exceptions as api_exceptions

Account = get_model('oscar_accounts', 'Account')


class SelectCreditAppView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )
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
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        serializer = self.get_serializer_class()(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            account = serializer.save()
        except core_exceptions.CreditApplicationDenied:
            raise api_exceptions.CreditApplicationDenied()

        serializer = AccountSerializer(account, context={'request': request})
        return Response(serializer.data)



class USCreditAppView(BaseCreditAppView):
    permission_classes = (IsAuthenticated, )
    serializer_class = USCreditAppSerializer



class USJointCreditAppView(BaseCreditAppView):
    permission_classes = (IsAuthenticated, )
    serializer_class = USJointCreditAppSerializer



class CACreditAppView(BaseCreditAppView):
    permission_classes = (IsAuthenticated, )
    serializer_class = CACreditAppSerializer



class CAJointCreditAppView(BaseCreditAppView):
    permission_classes = (IsAuthenticated, )
    serializer_class = CAJointCreditAppSerializer



class AccountView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, IsAccountOwner)
    model = Account
    serializer_class = AccountSerializer

    def get_queryset(self):
        ids = IsAccountOwner.list_valid_account_ids(self.request)
        return Account.objects.filter(id__in=ids).order_by('id').all()


class FinancingPlanView(views.APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        basket = operations.get_basket(request)
        plans = list_plans_for_basket(basket)
        ser = FinancingPlanSerializer(plans, many=True)
        return Response(ser.data)
