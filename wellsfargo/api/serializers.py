from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from oscar.core.loading import get_model
from ..connector import actions
from ..core.constants import (
    US, CA,
    INDIVIDUAL, JOINT,
    ENGLISH, FRENCH,
)
from ..models import (
    FinancingPlan,
    USCreditApp,
    USJointCreditApp,
    CACreditApp,
    CAJointCreditApp,
)

Basket = get_model('basket', 'Basket')
BillingAddress = get_model('order', 'BillingAddress')
PaymentEventType = get_model('order', 'PaymentEventType')
PaymentEvent = get_model('order', 'PaymentEvent')
PaymentEventQuantity = get_model('order', 'PaymentEventQuantity')
ShippingAddress = get_model('order', 'ShippingAddress')
Source = get_model('payment', 'Source')
SourceType = get_model('payment', 'SourceType')
Transaction = get_model('payment', 'Transaction')
Account = get_model('oscar_accounts', 'Account')


class AppSelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = USCreditApp
        fields = ('region', 'app_type')


class BaseCreditAppSerializer(serializers.ModelSerializer):
    def save(self):
        request = self.context['request']

        # Build application class and save record to DB to record the attempt
        Application = self.Meta.model
        app = Application(**self.validated_data)
        app.user = request.user
        app.save()

        # Submit application to to Wells
        resp = actions.submit_credit_application(app)

        # Use the Wells response to create a new account in the DB (if the application was approved)
        account = resp.save(owner=request.user)
        return account


class USCreditAppSerializer(BaseCreditAppSerializer):
    region = serializers.ChoiceField(default=US, choices=(
        (US, _('United States')),
    ))
    app_type = serializers.ChoiceField(default=INDIVIDUAL, choices=(
        (INDIVIDUAL, _('Individual')),
    ))
    language = serializers.ChoiceField(default=ENGLISH, choices=(
        (ENGLISH, _('English')),
    ))

    class Meta:
        model = USCreditApp
        exclude = ('user', )


class USJointCreditAppSerializer(BaseCreditAppSerializer):
    region = serializers.ChoiceField(default=US, choices=(
        (US, _('United States')),
    ))
    app_type = serializers.ChoiceField(default=JOINT, choices=(
        (JOINT, _('Joint')),
    ))
    language = serializers.ChoiceField(default=ENGLISH, choices=(
        (ENGLISH, _('English')),
    ))

    class Meta:
        model = USJointCreditApp
        exclude = ('user', )


class CACreditAppSerializer(BaseCreditAppSerializer):
    region = serializers.ChoiceField(default=CA, choices=(
        (CA, _('Canada')),
    ))
    app_type = serializers.ChoiceField(default=INDIVIDUAL, choices=(
        (INDIVIDUAL, _('Individual')),
    ))
    language = serializers.ChoiceField(default=ENGLISH, choices=(
        (ENGLISH, _('English')),
        (FRENCH, _('French')),
    ))

    class Meta:
        model = CACreditApp
        exclude = ('user', )


class CAJointCreditAppSerializer(BaseCreditAppSerializer):
    region = serializers.ChoiceField(default=CA, choices=(
        (CA, _('Canada')),
    ))
    app_type = serializers.ChoiceField(default=JOINT, choices=(
        (JOINT, _('Joint')),
    ))
    language = serializers.ChoiceField(default=ENGLISH, choices=(
        (ENGLISH, _('English')),
        (FRENCH, _('French')),
    ))

    class Meta:
        model = CAJointCreditApp
        exclude = ('user', )


class AccountSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='wfrs-api-account-detail')

    account_type = serializers.PrimaryKeyRelatedField(read_only=True)
    account_type_name = serializers.CharField(source='account_type.name', read_only=True)

    primary_user = serializers.SlugRelatedField(read_only=True, slug_field='username')
    secondary_users = serializers.SlugRelatedField(many=True, read_only=True, slug_field='username')

    locale = serializers.CharField(source='wfrs_metadata.locale', read_only=True)
    account_number = serializers.CharField(source='wfrs_metadata.account_number', read_only=True)

    class Meta:
        model = Account
        fields = (
            'id',
            'url',
            'account_type',
            'account_type_name',
            'name',
            'description',
            'code',
            'status',
            'primary_user',
            'secondary_users',
            'credit_limit',
            'balance',
            'start_date',
            'end_date',
            'locale',
            'account_number',
        )
        extra_kwargs = {
            'balance': { 'read_only': True }
        }


class FinancingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancingPlan
        fields = (
            'id',
            'plan_number',
            'description',
            'apr',
            'term_months',
        )
