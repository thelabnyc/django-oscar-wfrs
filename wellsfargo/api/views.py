from rest_framework.response import Response
from rest_framework.reverse import reverse_lazy
from rest_framework import (
    viewsets,
    generics,
)
from oscar.core.loading import get_model
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
)
from .permissions import IsAccountOwner, add_session_account
from ..core import exceptions as core_exceptions
from . import exceptions as api_exceptions

Account = get_model('oscar_accounts', 'Account')


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
        except core_exceptions.CreditApplicationDenied:
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
