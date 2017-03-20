from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from oscar.core.loading import get_model
from ..connector import actions
from ..core.constants import (
    US, CA,
    INDIVIDUAL, JOINT,
    ENGLISH, FRENCH,
)
from ..core import exceptions as core_exceptions
from ..models import (
    FinancingPlan,
    USCreditApp,
    USJointCreditApp,
    CACreditApp,
    CAJointCreditApp,
)
from . import exceptions as api_exceptions

Basket = get_model('basket', 'Basket')
BillingAddress = get_model('order', 'BillingAddress')
PaymentEventType = get_model('order', 'PaymentEventType')
PaymentEvent = get_model('order', 'PaymentEvent')
PaymentEventQuantity = get_model('order', 'PaymentEventQuantity')
ShippingAddress = get_model('order', 'ShippingAddress')
Source = get_model('payment', 'Source')
SourceType = get_model('payment', 'SourceType')
Transaction = get_model('payment', 'Transaction')


class AppSelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = USCreditApp
        fields = ('region', 'app_type')


class BaseCreditAppSerializer(serializers.ModelSerializer):
    def save(self):
        request = self.context['request']

        request_user = None
        if request.user and request.user.is_authenticated():
            request_user = request.user

        # Build application class and save record to DB to record the attempt
        Application = self.Meta.model
        app = Application(**self.validated_data)
        app.user = request_user
        app.submitting_user = request_user
        app.save()

        # Submit application to to Wells
        try:
            result = actions.submit_credit_application(app, current_user=request_user)
        except core_exceptions.CreditApplicationPending:
            raise api_exceptions.CreditApplicationPending()
        except core_exceptions.CreditApplicationDenied:
            raise api_exceptions.CreditApplicationDenied()
        except DjangoValidationError as e:
            raise DRFValidationError({
                'non_field_errors': [e.message]
            })

        # Update resulting account number
        app.account_number = result.account_number
        app.save()

        return result


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


class FinancingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancingPlan
        fields = (
            'id',
            'plan_number',
            'description',
            'apr',
            'term_months',
            'allow_credit_application',
        )


class AccountSerializer(serializers.Serializer):
    account_number = serializers.RegexField('^[0-9]{16}$', max_length=16, min_length=16)
    credit_limit = serializers.DecimalField(decimal_places=2, max_digits=12)
    balance = serializers.DecimalField(decimal_places=2, max_digits=12)
    open_to_buy = serializers.DecimalField(decimal_places=2, max_digits=12)
