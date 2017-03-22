from haystack import indexes
from oscar.core.loading import get_model
from .methods import WellsFargo
from .models import (
    TransferMetadata,
    USCreditApp,
    USJointCreditApp,
    CACreditApp,
    CAJointCreditApp,
)


Transaction = get_model('payment', 'Transaction')


class BaseCreditAppIndex(indexes.SearchIndex):
    APP_TYPE_CODE = indexes.CharField(model_attr='APP_TYPE_CODE')
    merchant_name = indexes.CharField()
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

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_merchant_name(self, obj):
        return obj.credentials.name if obj.credentials else None

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
