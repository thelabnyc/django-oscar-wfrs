from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from oscar.core.loading import get_model
from oscarapi.serializers import InlineBillingAddressSerializer
from ..connector import actions
from ..core.constants import (
    US, CA,
    INDIVIDUAL, JOINT,
    ENGLISH, FRENCH,
    LOCALE_CHOICES, EN_US
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
        resp = actions.submit_credit_application(app, current_user=request.user)

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
    locale = serializers.ChoiceField(source='wfrs_metadata.locale', choices=LOCALE_CHOICES, default=EN_US)
    account_number = serializers.RegexField('^[0-9]{16}$', max_length=16, min_length=16, source='wfrs_metadata.account_number')
    billing_address = InlineBillingAddressSerializer(source='wfrs_metadata.billing_address', required=False)

    class Meta:
        model = Account
        fields = (
            'id',
            'url',
            'name',
            'description',
            'code',
            'status',
            'credit_limit',
            'balance',
            'locale',
            'account_number',
            'billing_address',
        )
        extra_kwargs = {
            'name': { 'read_only': True },
            'description': { 'read_only': True },
            'code': { 'read_only': True },
            'status': { 'read_only': True },
            'credit_limit': { 'read_only': True },
            'balance': { 'read_only': True },
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
