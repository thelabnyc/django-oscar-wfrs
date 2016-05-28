from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from oscar.core.loading import get_model
from oscarapi.serializers.checkout import CheckoutSerializer as OscarCheckoutSerializer
from oscarapi.basket.operations import get_basket
from ..connector import actions
from ..core.constants import (
    US, CA,
    INDIVIDUAL, JOINT,
    LOCALE_CHOICES,
    ENGLISH, FRENCH,
    LOCALES,
    APP_TYPES, LANGUAGES, REGIONS
)
from ..core import exceptions as core_exceptions
from ..core.structures import (
    TransactionRequest,
    USCreditApp,
    USJointCreditApp,
    CACreditApp,
    CAJointCreditApp,
)
from ..settings import (
    WFRS_ACCOUNT_TYPE,
    WFRS_AUTH_PLAN_NUM,
    WFRS_PAYMENT_SOURCE,
    WFRS_TRANSACTION_STATUS,
    WFRS_INITIAL_ORDER_STATUS
)
from .permissions import IsAccountOwner
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
Account = get_model('oscar_accounts', 'Account')



class CheckoutSerializer(OscarCheckoutSerializer):
    _base_account_queryset = Account.active.filter(account_type__name=WFRS_ACCOUNT_TYPE)
    wfrs_source_account = serializers.PrimaryKeyRelatedField(queryset=_base_account_queryset)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # We require a request because we need to know what accounts are valid for the
        # user to be drafting from. This is derived from the user when authenticated or
        # the session store when anonymous
        request = self.context.get('request', None)
        assert request is not None, (
            "`%s` requires the request in the serializer"
            " context. Add `context={'request': request}` when instantiating "
            "the serializer." % self.__class__.__name__
        )

        # Limit baskets to only the one that is active and owned by the user.
        basket = get_basket(request)
        self.fields['basket'].queryset = Basket.objects.filter(pk=basket.pk)

        # Limit account to only those owned by the user
        valid_account_ids = IsAccountOwner.list_valid_account_ids(request)
        valid_accounts = self._base_account_queryset.filter(pk__in=valid_account_ids)
        self.fields['wfrs_source_account'].queryset = valid_accounts

    def get_initial_order_status(self, basket):
        return WFRS_INITIAL_ORDER_STATUS

    @transaction.atomic()
    def create(self, validated_data):
        request = self.context['request']

        total = validated_data.get('total')
        basket = validated_data.get('basket')
        order_number = self.generate_order_number(basket)

        # Perform an authorization with WFRS
        account = validated_data.get('wfrs_source_account')
        transfer = self._do_auth_transaction(request, account, total.incl_tax, order_number)

        billing_address = None
        if 'billing_address' in validated_data:
            billing_address = BillingAddress(**validated_data['billing_address'])

        shipping_address = None
        if 'shipping_address' in validated_data:
            shipping_address = ShippingAddress(**validated_data['shipping_address'])

        # Place the order
        order = self._place_order(
            order_number=order_number,
            user=request.user,
            basket=basket,
            order_total=total,
            billing_address=billing_address,
            shipping_address=shipping_address,
            shipping_method=validated_data.get('shipping_method'),
            shipping_charge=validated_data.get('shipping_charge'),
            guest_email=validated_data.get('guest_email') or '')

        # Record a transaction and payment event for the order
        self._record_payment(order, transfer)

        # Return the order
        return order

    def _do_auth_transaction(self, request, account, amount, order_number=None):
        user = request.user if request.user.is_authenticated() else None
        transaction_request = TransactionRequest.build_auth_request(
            source_account=account,
            plan_number=WFRS_AUTH_PLAN_NUM,
            amount=amount,
            ticket_number=order_number,
            user=user)
        try:
            transfer = actions.submit_transaction(transaction_request)
        except core_exceptions.TransactionDenied as e:
            raise api_exceptions.TransactionDenied()
        return transfer

    def _place_order(self, **kwargs):
        try:
            order = self.place_order(**kwargs)
        except ValueError as e:
            raise exceptions.NotAcceptable(e.message)
        return order

    def _record_payment(self, order, transfer):
        source_type, created = SourceType.objects.get_or_create(name=WFRS_PAYMENT_SOURCE)
        source, created = Source.objects.get_or_create(order=order, source_type=source_type)
        source.currency = order.currency
        source.amount_allocated += transfer.amount
        source.save()

        txn = Transaction()
        txn.source = source
        txn.txn_type = Transaction.AUTHORISE
        txn.amount = transfer.amount
        txn.reference = transfer.merchant_reference
        txn.status = WFRS_TRANSACTION_STATUS
        txn.save()

        event = PaymentEvent()
        event.order = order
        event.amount = transfer.amount
        event.reference = transfer.merchant_reference
        event.event_type = PaymentEventType.objects.get_or_create(name=Transaction.AUTHORISE)[0]
        event.save()

        for line in order.lines.all():
            line_event = PaymentEventQuantity()
            line_event.event = event
            line_event.line = line
            line_event.quantity = line.quantity
            line_event.save()


class AppSelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = USCreditApp
        fields = ('region', 'app_type')


class BaseCreditAppSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        request = self.context['request']

        # Build application class
        Application = self.Meta.model
        app = Application(**validated_data)

        # Sub to WF
        resp = actions.submit_credit_application(app)

        # Save and return an account
        owner = None
        if hasattr(request, 'user') and request.user.is_authenticated():
            owner = request.user
        return resp.save(owner)


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
