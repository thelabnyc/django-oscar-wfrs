from rest_framework import serializers
from oscar.core.loading import get_model
from oscarapicheckout.methods import PaymentMethod, PaymentMethodSerializer
from oscarapicheckout.states import Complete, Declined
from .api.permissions import IsAccountOwner
from .connector import actions
from .core import exceptions
from .core.structures import TransactionRequest
from .settings import WFRS_ACCOUNT_TYPE, WFRS_AUTH_PLAN_NUM

Account = get_model('oscar_accounts', 'Account')


class WellsFargoPaymentMethodSerializer(PaymentMethodSerializer):
    _base_account_queryset = Account.active.filter(account_type__name=WFRS_ACCOUNT_TYPE)
    account = serializers.PrimaryKeyRelatedField(queryset=_base_account_queryset)

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

        # Limit account to only those owned by the user
        valid_account_ids = IsAccountOwner.list_valid_account_ids(request)
        valid_accounts = self._base_account_queryset.filter(pk__in=valid_account_ids)
        self.fields['account'].queryset = valid_accounts


class WellsFargo(PaymentMethod):
    name = 'Wells Fargo'
    code = 'wells-fargo'
    serializer_class = WellsFargoPaymentMethodSerializer


    def _record_payment(self, request, order, amount, reference, account, **kwargs):
        # Figure out how much to authorize
        source = self.get_source(order, reference)
        amount_to_allocate = amount - source.amount_allocated

        # Perform an authorization with WFRS
        transaction_request = TransactionRequest.build_auth_request(
            source_account=account,
            plan_number=WFRS_AUTH_PLAN_NUM,
            amount=amount_to_allocate,
            ticket_number=order.number,
            user=order.user)
        try:
            transfer = actions.submit_transaction(transaction_request)
        except exceptions.TransactionDenied:
            return Declined(amount)

        # Record the allocation and payment event
        source.allocate(amount_to_allocate, transfer.merchant_reference)
        event = self.make_authorize_event(order, amount_to_allocate, transfer.merchant_reference)
        for line in order.lines.all():
            self.make_event_quantity(event, line, line.quantity)

        return Complete(source.amount_allocated)
