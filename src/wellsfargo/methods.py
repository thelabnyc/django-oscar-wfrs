from django.core.exceptions import ValidationError
from rest_framework import serializers
from oscarapi.basket import operations
from oscarapicheckout.methods import PaymentMethod, PaymentMethodSerializer
from oscarapicheckout.states import Complete, Declined
from .connector import actions
from .core.structures import TransactionRequest
from .core import exceptions
from .utils import list_plans_for_basket
from .models import FinancingPlan


class WellsFargoPaymentMethodSerializer(PaymentMethodSerializer):
    account_number = serializers.RegexField('^[0-9]{16}$', max_length=16, min_length=16)
    financing_plan = serializers.PrimaryKeyRelatedField(queryset=FinancingPlan.objects.get_queryset())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # We require a request because we need to know what plans are valid for the
        # user to be drafting from. This is tied to the current basket.
        request = self.context.get('request', None)
        assert request is not None, (
            "`%s` requires the request in the serializer"
            " context. Add `context={'request': request}` when instantiating "
            "the serializer." % self.__class__.__name__
        )

        # Limit plans by the user's basket (plan availability is driven by offer/voucher conditions)
        basket = operations.get_basket(self.context['request'])
        plans = list_plans_for_basket(basket)
        self.fields['financing_plan'].queryset = FinancingPlan.objects.filter(id__in=[p.id for p in plans])


class WellsFargo(PaymentMethod):
    name = 'Wells Fargo'
    code = 'wells-fargo'
    serializer_class = WellsFargoPaymentMethodSerializer

    def _record_payment(self, request, order, amount, reference, account_number, financing_plan, **kwargs):
        # Figure out how much to authorize
        source = self.get_source(order, reference)
        amount_to_allocate = amount - source.amount_allocated

        # Perform an authorization with WFRS
        trans_request = TransactionRequest()
        trans_request.user = order.user
        trans_request.account_number = account_number
        trans_request.plan_number = financing_plan.plan_number
        trans_request.amount = amount_to_allocate
        trans_request.ticket_number = order.number

        request_user = None
        if request.user and request.user.is_authenticated():
            request_user = request.user

        try:
            transfer = actions.submit_transaction(trans_request, current_user=request_user)
        except (exceptions.TransactionDenied, ValidationError):
            return Declined(amount)

        # Record the allocation and payment event
        source.allocate(amount_to_allocate, transfer.merchant_reference)
        event = self.make_authorize_event(order, amount_to_allocate, transfer.merchant_reference)
        for line in order.lines.all():
            self.make_event_quantity(event, line, line.quantity)

        return Complete(source.amount_allocated)
