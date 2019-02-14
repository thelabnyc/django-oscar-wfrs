from haystack import indexes
from oscar.core.loading import get_model
from .methods import WellsFargo
from .models import (
    TransferMetadata,
    USCreditApp,
    USJointCreditApp,
    CACreditApp,
    CAJointCreditApp,
    PreQualificationRequest,
)


Transaction = get_model('payment', 'Transaction')


class BaseCreditAppIndex(indexes.SearchIndex):
    APP_TYPE_CODE = indexes.CharField(model_attr='APP_TYPE_CODE')
    merchant_name = indexes.CharField()
    status = indexes.CharField(model_attr='status')
    status_name = indexes.CharField(model_attr='status')
    application_source = indexes.CharField(model_attr='application_source')
    modified_datetime = indexes.DateTimeField(model_attr='modified_datetime')
    created_datetime = indexes.DateTimeField(model_attr='created_datetime')

    account_number = indexes.CharField(model_attr='account_number', null=True)
    purchase_price = indexes.CharField(model_attr='purchase_price', null=True)
    credit_limit = indexes.CharField(null=True)
    order_total = indexes.CharField(null=True)
    order_merchant_name = indexes.CharField(null=True)
    order_placed = indexes.DateTimeField(null=True)

    main_first_name = indexes.CharField(model_attr='main_first_name')
    main_last_name = indexes.CharField(model_attr='main_last_name')
    email = indexes.CharField(model_attr='email')

    user_full_name = indexes.CharField(null=True)
    user_username = indexes.CharField(null=True)
    user_id = indexes.IntegerField(null=True)

    submitting_user_full_name = indexes.CharField(null=True)
    submitting_user_username = indexes.CharField(null=True)
    submitting_user_id = indexes.IntegerField(null=True)

    name = indexes.EdgeNgramField(use_template=True, template_name='search/indexes/wellsfargo/application_name.txt')
    address = indexes.EdgeNgramField(use_template=True, template_name='search/indexes/wellsfargo/application_address.txt')
    phone = indexes.EdgeNgramField(use_template=True, template_name='search/indexes/wellsfargo/application_phone.txt')

    text = indexes.EdgeNgramField(document=True, use_template=True, template_name='search/indexes/wellsfargo/application_text.txt')

    def get_updated_field(self):
        return 'modified_datetime'

    def index_queryset(self, using=None):
        qs = self.get_model().objects\
                             .select_related('credentials', 'user', 'submitting_user')\
                             .all()
        return qs

    def prepare_merchant_name(self, obj):
        return obj.credentials.name if obj.credentials else None

    def prepare_status_name(self, obj):
        return obj.get_status_display()

    def prepare_credit_limit(self, obj):
        return obj.get_credit_limit()

    def prepare_order_total(self, obj):
        order = obj.get_first_order()
        if not order:
            return None
        return order.total_incl_tax

    def prepare_order_merchant_name(self, obj):
        order = obj.get_first_order()
        if not order:
            return None
        transfers = []
        for source in order.sources.filter(source_type__name=WellsFargo.name).all():
            for transaction in source.transactions.filter(txn_type=Transaction.AUTHORISE).all():
                transfer = TransferMetadata.get_by_oscar_transaction(transaction)
                if transfer:
                    transfers.append(transfer)
        if len(transfers) <= 0:
            return None
        credentials = transfers[0].credentials
        return credentials.name if credentials else None

    def prepare_order_placed(self, obj):
        order = obj.get_first_order()
        if not order:
            return None
        return order.date_placed

    def prepare_user_full_name(self, obj):
        return obj.user.get_full_name() if obj.user else None

    def prepare_user_username(self, obj):
        return obj.user.username if obj.user else None

    def prepare_user_id(self, obj):
        return obj.user.pk if obj.user else None

    def prepare_submitting_user_full_name(self, obj):
        return obj.submitting_user.get_full_name() if obj.submitting_user else None

    def prepare_submitting_user_username(self, obj):
        return obj.submitting_user.username if obj.submitting_user else None

    def prepare_submitting_user_id(self, obj):
        return obj.submitting_user.pk if obj.submitting_user else None


class BaseJointCreditAppIndex(BaseCreditAppIndex):
    joint_first_name = indexes.CharField(model_attr='joint_first_name')
    joint_last_name = indexes.CharField(model_attr='joint_last_name')


class USCreditAppIndex(BaseCreditAppIndex, indexes.Indexable):
    def get_model(self):
        return USCreditApp


class USJointCreditAppIndex(BaseJointCreditAppIndex, indexes.Indexable):
    def get_model(self):
        return USJointCreditApp


class CACreditAppIndex(BaseCreditAppIndex, indexes.Indexable):
    def get_model(self):
        return CACreditApp


class CAJointCreditAppIndex(BaseJointCreditAppIndex, indexes.Indexable):
    def get_model(self):
        return CAJointCreditApp


class TransferMetadataIndex(indexes.SearchIndex, indexes.Indexable):
    modified_datetime = indexes.DateTimeField(model_attr='modified_datetime')
    created_datetime = indexes.DateTimeField(model_attr='created_datetime')

    user_full_name = indexes.CharField(null=True)
    user_username = indexes.CharField(null=True)
    user_id = indexes.IntegerField(null=True)

    merchant_reference = indexes.CharField(model_attr='merchant_reference', null=True)
    masked_account_number = indexes.CharField(model_attr='masked_account_number')
    order_number = indexes.CharField(null=True)
    amount = indexes.DecimalField(model_attr='amount')
    type_code = indexes.CharField(model_attr='type_code')
    type_code_name = indexes.CharField(model_attr='type_name')
    ticket_number = indexes.CharField(model_attr='ticket_number', null=True)
    financing_plan_number = indexes.IntegerField(null=True)
    auth_number = indexes.CharField(model_attr='auth_number', null=True)
    status = indexes.CharField(model_attr='status')
    status_name = indexes.CharField(model_attr='status_name')
    message = indexes.CharField(model_attr='message')
    disclosure = indexes.CharField(model_attr='disclosure')

    text = indexes.EdgeNgramField(document=True, use_template=True, template_name='search/indexes/wellsfargo/transfer_text.txt')

    def get_model(self):
        return TransferMetadata

    def get_updated_field(self):
        return 'modified_datetime'

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_order_number(self, obj):
        order = obj.get_order()
        return order.number if order else None

    def prepare_financing_plan_number(self, obj):
        return obj.financing_plan.plan_number if obj.financing_plan else None

    def prepare_user_full_name(self, obj):
        return obj.user.get_full_name() if obj.user else None

    def prepare_user_username(self, obj):
        return obj.user.username if obj.user else None

    def prepare_user_id(self, obj):
        return obj.user.pk if obj.user else None



class PreQualificationIndex(indexes.SearchIndex, indexes.Indexable):
    uuid = indexes.CharField(model_attr='uuid')
    customer_initiated = indexes.BooleanField(model_attr='customer_initiated')
    email = indexes.CharField(model_attr='email', null=True)
    first_name = indexes.CharField(model_attr='first_name')
    middle_initial = indexes.CharField(model_attr='middle_initial', null=True)
    last_name = indexes.CharField(model_attr='last_name')
    line1 = indexes.CharField(model_attr='line1')
    line2 = indexes.CharField(model_attr='line2', null=True)
    city = indexes.CharField(model_attr='city')
    state = indexes.CharField(model_attr='state')
    postcode = indexes.CharField(model_attr='postcode')
    phone = indexes.CharField(model_attr='phone')
    created_datetime = indexes.DateTimeField(model_attr='created_datetime')

    merchant_name = indexes.CharField(null=True)
    merchant_num = indexes.CharField(null=True)

    response_status = indexes.CharField(model_attr='status')
    response_status_name = indexes.CharField(model_attr='status_name')
    response_credit_limit = indexes.CharField(null=True)
    response_customer_response = indexes.CharField(null=True)
    response_reported_datetime = indexes.DateTimeField(null=True)

    sdk_application_result = indexes.CharField(null=True)

    order_total = indexes.CharField(null=True)
    order_date_placed = indexes.DateTimeField(null=True)
    order_merchant_name = indexes.CharField(null=True)

    text = indexes.EdgeNgramField(document=True, use_template=True, template_name='search/indexes/wellsfargo/prequalification_text.txt')

    def get_model(self):
        return PreQualificationRequest

    def get_updated_field(self):
        return 'modified_datetime'

    def index_queryset(self, using=None):
        _related = [
            'credentials',
            'response',
            'response__customer_order',
            'response__sdk_application_result'
        ]
        qs = self.get_model().objects\
                             .select_related(*_related)\
                             .all()
        return qs

    def prepare_merchant_name(self, obj):
        return obj.credentials.name if obj.credentials else None

    def prepare_merchant_num(self, obj):
        return obj.credentials.merchant_num if obj.credentials else None

    def prepare_response_credit_limit(self, obj):
        resp = getattr(obj, 'response', None)
        if resp is None:
            return None
        return resp.credit_limit

    def prepare_response_customer_response(self, obj):
        resp = getattr(obj, 'response', None)
        if resp is None:
            return None
        return resp.customer_response

    def prepare_response_reported_datetime(self, obj):
        resp = getattr(obj, 'response', None)
        if resp is None:
            return None
        return resp.reported_datetime

    def prepare_sdk_application_result(self, obj):
        resp = getattr(obj, 'response', None)
        if resp is None:
            return None
        app_result = getattr(resp, 'sdk_application_result', None)
        if app_result is None:
            return None
        return app_result.application_status

    def prepare_order_total(self, obj):
        return obj.resulting_order.total_incl_tax if obj.resulting_order else None

    def prepare_order_date_placed(self, obj):
        return obj.resulting_order.date_placed if obj.resulting_order else None

    def prepare_order_merchant_name(self, obj):
        order = obj.resulting_order
        if not order:
            return None
        transfers = []
        for source in order.sources.filter(source_type__name=WellsFargo.name).all():
            for transaction in source.transactions.filter(txn_type=Transaction.AUTHORISE).all():
                transfer = TransferMetadata.get_by_oscar_transaction(transaction)
                if transfer:
                    transfers.append(transfer)
        if len(transfers) <= 0:
            return None
        credentials = transfers[0].credentials
        return credentials.name if credentials else None
