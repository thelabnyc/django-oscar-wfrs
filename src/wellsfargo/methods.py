from django.core.exceptions import ValidationError
from rest_framework import serializers
from oscarapi.basket import operations
from oscarapicheckout.methods import PaymentMethod, PaymentMethodSerializer
from oscarapicheckout.states import Complete, Declined
from requests.exceptions import Timeout, ConnectionError
from .connector import actions
from .core.constants import TRANS_TYPE_AUTH, TRANS_TYPE_CANCEL_AUTH
from .core.structures import TransactionRequest
from .core import exceptions
from .utils import list_plans_for_basket
from .models import FraudScreenResult, FinancingPlan
from .fraud import screen_transaction
from .settings import WFRS_MAX_TRANSACTION_ATTEMPTS
import logging

logger = logging.getLogger(__name__)


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

    def _record_payment(self, request, order, method_key, amount, reference, account_number, financing_plan, **kwargs):
        # Figure out how much to authorize
        source = self.get_source(order, reference)

        # Build a transaction request
        trans_request = self._build_trans_request(
            order=order,
            account_number=account_number,
            plan_number=financing_plan.plan_number,
            amount=amount,
            type_code=TRANS_TYPE_AUTH)

        # Build a cancel transaction request in-case the transaction request fails.
        cancel_trans_request = self._build_trans_request(
            order=order,
            account_number=account_number,
            plan_number=financing_plan.plan_number,
            amount=amount,
            type_code=TRANS_TYPE_CANCEL_AUTH)

        # If Fraud Screening is enabled, run it and see if the transaction passes muster.
        fraud_response = screen_transaction(request, order)
        if fraud_response.decision not in (FraudScreenResult.DECISION_ACCEPT, FraudScreenResult.DECISION_REVIEW):
            logger.info('WFRS transaction for Order[{}] failed fraud screen. Reason: {}'.format(order.number, fraud_response.message))
            return Declined(amount)

        # Figure out which WFRS credentials to use based on the user
        request_user = None
        if request.user and request.user.is_authenticated:
            request_user = request.user

        # Perform an authorization with WFRS
        try:
            transfer = self._perform_auth_transaction(
                trans_request=trans_request,
                cancel_trans_request=cancel_trans_request,
                current_user=request_user,
                transaction_uuid=fraud_response.reference)
        except (exceptions.TransactionDenied, ValidationError) as e:
            logger.info('WFRS transaction failed for Order[{}]. Reason: {}'.format(order.number, str(e)))
            return Declined(amount)

        # Record the allocation as a transaction
        source.allocate(amount,
            reference=transfer.merchant_reference,
            status=fraud_response.decision)

        # Record the payment event
        event = self.make_authorize_event(order, amount, transfer.merchant_reference)
        for line in order.lines.all():
            self.make_event_quantity(event, line, line.quantity)

        return Complete(source.amount_allocated)


    def _perform_auth_transaction(self, trans_request, cancel_trans_request, current_user, transaction_uuid, max_attempts=WFRS_MAX_TRANSACTION_ATTEMPTS):
        exc = None
        for i in range(max_attempts):
            # Try to submit the transaction
            try:
                transfer = actions.submit_transaction(trans_request, current_user=current_user, transaction_uuid=transaction_uuid)
                return transfer

            # If the transaction times out for some reason, cancel it and then try again.
            except (Timeout, ConnectionError) as e:
                exc = e
                logger.warning('WFRS transaction failed for Order[{}]: {}'.format(trans_request.ticket_number, e))
                actions.submit_transaction(cancel_trans_request, current_user=current_user, transaction_uuid=transaction_uuid, persist=False)
                logger.warning('Canceled transaction for Order[{}] due to previous error.'.format(trans_request.ticket_number))

        # We couldn't perform the transaction successfully in the allotted time, so bubble up the last exception thrown.
        raise exc


    def _build_trans_request(self, order, account_number, plan_number, amount, type_code=TRANS_TYPE_AUTH):
        trans_request = TransactionRequest()
        trans_request.type_code = type_code
        trans_request.user = order.user
        trans_request.account_number = account_number
        trans_request.plan_number = plan_number
        trans_request.amount = amount
        trans_request.ticket_number = order.number
        return trans_request
