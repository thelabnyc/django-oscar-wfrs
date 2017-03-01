from rest_framework.response import Response
from rest_framework.reverse import reverse_lazy
from rest_framework import views, generics
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
from ..utils import list_plans_for_basket


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
        app_result = serializer.save()
        serializer = AccountSerializer(app_result)
        return Response(serializer.data)


class USCreditAppView(BaseCreditAppView):
    serializer_class = USCreditAppSerializer


class USJointCreditAppView(BaseCreditAppView):
    serializer_class = USJointCreditAppSerializer


class CACreditAppView(BaseCreditAppView):
    serializer_class = CACreditAppSerializer


class CAJointCreditAppView(BaseCreditAppView):
    serializer_class = CAJointCreditAppSerializer


class FinancingPlanView(views.APIView):
    def get(self, request):
        basket = operations.get_basket(request)
        plans = list_plans_for_basket(basket)
        ser = FinancingPlanSerializer(plans, many=True)
        return Response(ser.data)
