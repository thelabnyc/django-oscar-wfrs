from django.db.models import Q
from haystack import indexes
from .models import (
    AccountOwner,
    USCreditApp,
    USJointCreditApp,
    CACreditApp,
    CAJointCreditApp,
)


class AccountOwnerAutocompleteIndex(indexes.SearchIndex, indexes.Indexable):
    user_id = indexes.IntegerField(model_attr='pk', indexed=False, stored=True)
    username = indexes.CharField(model_attr='username', indexed=False, stored=True)
    first_name = indexes.CharField(model_attr='first_name', indexed=False, stored=True)
    last_name = indexes.CharField(model_attr='last_name', indexed=False, stored=True)
    email = indexes.CharField(model_attr='email', indexed=False, stored=True)

    text = indexes.EdgeNgramField(document=True, use_template=True, template_name='search/indexes/wellsfargo/accountowner_text.txt')

    def get_model(self):
        return AccountOwner

    def index_queryset(self, using=None):
        blank_first_name = Q(first_name=None) | Q(first_name='')
        blank_last_name = Q(last_name=None) | Q(last_name='')
        blank_email = Q(email=None) | Q(email='')
        # If we don't have at least a name or an email, don't include them in the search index
        qs = self.get_model().objects.exclude(blank_first_name & blank_last_name & blank_email)
        return qs.all()


class BaseCreditAppIndex(indexes.SearchIndex):
    APP_TYPE_CODE = indexes.CharField(model_attr='APP_TYPE_CODE')
    modified_datetime = indexes.DateTimeField(model_attr='modified_datetime')
    created_datetime = indexes.DateTimeField(model_attr='created_datetime')

    main_first_name = indexes.CharField(model_attr='main_first_name')
    main_last_name = indexes.CharField(model_attr='main_last_name')
    email = indexes.CharField(model_attr='email')

    user_full_name = indexes.CharField()
    user_username = indexes.CharField()
    user_id = indexes.IntegerField()

    submitting_user_full_name = indexes.CharField(null=True)
    submitting_user_username = indexes.CharField(null=True)
    submitting_user_id = indexes.IntegerField(null=True)

    account_id = indexes.IntegerField(null=True)
    account_name = indexes.CharField(null=True)

    name = indexes.EdgeNgramField(use_template=True, template_name='search/indexes/wellsfargo/application_name.txt')
    address = indexes.EdgeNgramField(use_template=True, template_name='search/indexes/wellsfargo/application_address.txt')
    phone = indexes.EdgeNgramField(use_template=True, template_name='search/indexes/wellsfargo/application_phone.txt')

    text = indexes.EdgeNgramField(document=True, use_template=True, template_name='search/indexes/wellsfargo/application_text.txt')

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_user_full_name(self, obj):
        return obj.user.get_full_name()

    def prepare_user_username(self, obj):
        return obj.user.username

    def prepare_user_id(self, obj):
        return obj.user.pk

    def prepare_submitting_user_full_name(self, obj):
        return obj.submitting_user.get_full_name() if obj.submitting_user else None

    def prepare_submitting_user_username(self, obj):
        return obj.submitting_user.username if obj.submitting_user else None

    def prepare_submitting_user_id(self, obj):
        return obj.submitting_user.pk if obj.submitting_user else None

    def prepare_account_id(self, obj):
        return obj.account.id if obj.account else None

    def prepare_account_name(self, obj):
        return obj.account.name if obj.account else None


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
