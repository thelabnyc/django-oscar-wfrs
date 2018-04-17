from datetime import timedelta
from decimal import Decimal as D
from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse
from oscar.core.loading import get_model
from oscar.test import factories
from wellsfargo.models import FinancingPlan, FinancingPlanBenefit, FraudScreenResult
from wellsfargo.tests.base import BaseTest
from wellsfargo.tests.test_fraud import patch_fraud_protection
from wellsfargo.tests import responses
from requests.exceptions import Timeout
import mock

ConditionalOffer = get_model('offer', 'ConditionalOffer')
Condition = get_model('offer', 'Condition')
Range = get_model('offer', 'Range')


class CheckoutTest(BaseTest):
    """Full Integration Test of Checkout"""
    def setUp(self):
        super().setUp()
        condition = Condition.objects.create(
            range=Range.objects.create(name='Everything', includes_all_products=True),
            type=Condition.VALUE,
            value='1.00')

        self.plan = FinancingPlan.objects.create(
            plan_number=9999,
            description='Pay for stuff sometime in the next 12 months',
            apr='9.95',
            term_months=12)
        benefit = FinancingPlanBenefit.objects.create(
            group_name='Financing is available')
        benefit.plans.add(self.plan)

        ConditionalOffer.objects.create(
            name='Financing is available',
            short_name='Financing',
            condition=condition,
            benefit=benefit,
            offer_type=ConditionalOffer.SITE,
            start_datetime=timezone.now() - timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1))


    @mock.patch('soap.get_transport')
    def test_checkout_authd(self, get_transport):
        """Full checkout process using minimal api calls"""

        def gt():
            return self._build_transport_with_reply(responses.transaction_successful, pattern='wellsfargo.com')
        get_transport.side_effect = gt

        self.client.login(username='joe', password='schmoe')

        # Should be successful
        basket_id = self._prepare_basket()
        self._check_available_plans()
        resp = self._checkout(basket_id, '9999999999999999')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self._fetch_payment_states()
        self.assertEqual(resp.data['order_status'], 'Authorized')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['status'], 'Consumed')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['amount'], '10.00')

        self.assertEqual(FraudScreenResult.objects.count(), 1)
        fraud_result = FraudScreenResult.objects.first()
        self.assertEqual(fraud_result.screen_type, 'Dummy')
        self.assertEqual(fraud_result.order.basket.pk, basket_id)
        self.assertEqual(fraud_result.decision, FraudScreenResult.DECISION_ACCEPT)
        self.assertEqual(fraud_result.message, 'Transaction accepted.')


    @mock.patch('soap.get_transport')
    def test_checkout_trans_declined(self, get_transport):
        """Full checkout process using minimal api calls"""

        def gt():
            return self._build_transport_with_reply(responses.transaction_denied, pattern='wellsfargo.com')
        get_transport.side_effect = gt

        self.client.login(username='joe', password='schmoe')

        # Should be successful
        basket_id = self._prepare_basket()
        self._check_available_plans()
        resp = self._checkout(basket_id, '9999999999999999')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self._fetch_payment_states()
        self.assertEqual(resp.data['order_status'], 'Payment Declined')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['status'], 'Declined')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['amount'], '10.00')



    @mock.patch('soap.get_transport')
    def test_checkout_with_authorization_timeout(self, get_transport):
        """Test checkout where the first call to WFRS times out, but the second succeeds."""
        context = { 'i': 0 }

        def gt():
            context['i'] += 1
            if context['i'] <= 1:
                raise Timeout()
            return self._build_transport_with_reply(responses.transaction_successful, pattern='wellsfargo.com')
        get_transport.side_effect = gt

        self.client.login(username='joe', password='schmoe')

        # Should be successful even though first request times out
        basket_id = self._prepare_basket()
        self._check_available_plans()
        resp = self._checkout(basket_id, '9999999999999999')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self._fetch_payment_states()
        self.assertEqual(resp.data['order_status'], 'Authorized')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['status'], 'Consumed')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['amount'], '10.00')

        self.assertEqual(FraudScreenResult.objects.count(), 1)
        fraud_result = FraudScreenResult.objects.first()
        self.assertEqual(fraud_result.screen_type, 'Dummy')
        self.assertEqual(fraud_result.order.basket.pk, basket_id)
        self.assertEqual(fraud_result.decision, FraudScreenResult.DECISION_ACCEPT)
        self.assertEqual(fraud_result.message, 'Transaction accepted.')


    @patch_fraud_protection('wellsfargo.fraud.dummy.DummyFraudProtection',
        decision=FraudScreenResult.DECISION_REJECT,
        message='Rejected transaction.')
    @mock.patch('soap.get_transport')
    def test_checkout_fraud_rejection(self, get_transport):
        """Full checkout process using minimal api calls"""

        def gt():
            return self._build_transport_with_reply(responses.transaction_successful, pattern='wellsfargo.com')
        get_transport.side_effect = gt

        self.client.login(username='joe', password='schmoe')

        # Should be declined due to the fraud rejection
        basket_id = self._prepare_basket()
        self._check_available_plans()
        resp = self._checkout(basket_id, '9999999999999999')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self._fetch_payment_states()
        self.assertEqual(resp.data['order_status'], 'Payment Declined')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['status'], 'Declined')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['amount'], '10.00')

        self.assertEqual(FraudScreenResult.objects.count(), 1)
        fraud_result = FraudScreenResult.objects.first()
        self.assertEqual(fraud_result.screen_type, 'Dummy')
        self.assertEqual(fraud_result.order.basket.pk, basket_id)
        self.assertEqual(fraud_result.decision, FraudScreenResult.DECISION_REJECT)
        self.assertEqual(fraud_result.message, 'Rejected transaction.')


    @patch_fraud_protection('wellsfargo.fraud.dummy.DummyFraudProtection',
        decision=FraudScreenResult.DECISION_REVIEW,
        message='Transaction flagged for manual review.')
    @mock.patch('soap.get_transport')
    def test_checkout_fraud_review_flag(self, get_transport):
        """Full checkout process using minimal api calls"""

        def gt():
            return self._build_transport_with_reply(responses.transaction_successful, pattern='wellsfargo.com')
        get_transport.side_effect = gt

        self.client.login(username='joe', password='schmoe')

        # Should be successful, but flagged in the dashboard for review
        basket_id = self._prepare_basket()
        self._check_available_plans()
        resp = self._checkout(basket_id, '9999999999999999')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self._fetch_payment_states()
        self.assertEqual(resp.data['order_status'], 'Authorized')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['status'], 'Consumed')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['amount'], '10.00')

        self.assertEqual(FraudScreenResult.objects.count(), 1)
        fraud_result = FraudScreenResult.objects.first()
        self.assertEqual(fraud_result.screen_type, 'Dummy')
        self.assertEqual(fraud_result.order.basket.pk, basket_id)
        self.assertEqual(fraud_result.decision, FraudScreenResult.DECISION_REVIEW)
        self.assertEqual(fraud_result.message, 'Transaction flagged for manual review.')


    @mock.patch('soap.get_transport')
    def test_checkout_anon(self, get_transport):
        """Full checkout process using minimal api calls"""

        def gt():
            return self._build_transport_with_reply(responses.transaction_successful, pattern='wellsfargo.com')
        get_transport.side_effect = gt

        # Should be successful
        basket_id = self._prepare_basket()
        self._check_available_plans()
        resp = self._checkout(basket_id, '9999999999999999')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self._fetch_payment_states()
        self.assertEqual(resp.data['order_status'], 'Authorized')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['status'], 'Consumed')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['amount'], '10.00')


    @mock.patch('soap.get_transport')
    def test_checkout_bad_plan_number(self, get_transport):
        """Full checkout process using minimal api calls"""

        def gt():
            return self._build_transport_with_reply(responses.transaction_successful, pattern='wellsfargo.com')
        get_transport.side_effect = gt

        self.client.login(username='joe', password='schmoe')

        # Should be successful
        basket_id = self._prepare_basket()
        self._check_available_plans()
        resp = self._checkout(basket_id, '9999999999999999', plan_id=self.plan.id + 1)
        self.assertEqual(resp.status_code, status.HTTP_406_NOT_ACCEPTABLE)


    def _create_product(self, price=D('10.00')):
        product = factories.create_product(
            title='My Product',
            product_class='My Product Class')
        record = factories.create_stockrecord(
            currency='USD',
            product=product,
            num_in_stock=10,
            price_excl_tax=price)
        factories.create_purchase_info(record)
        return product


    def _get_basket(self):
        url = reverse('api-basket')
        return self.client.get(url)


    def _add_to_basket(self, product_id, quantity=1):
        url = reverse('api-basket-add-product')
        data = {
            "url": reverse('product-detail', args=[product_id]),
            "quantity": quantity
        }
        return self.client.post(url, data)


    def _prepare_basket(self):
        product = self._create_product()
        resp = self._add_to_basket(product.id)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self._get_basket()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        basket_id = resp.data['id']

        lines_url = resp.data['lines']
        resp = self.client.get(lines_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        return basket_id


    def _check_available_plans(self):
        url = reverse('wfrs-api-plan-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['plan_number'], 9999)


    def _checkout(self, basket_id, account_number, plan_id=None):
        if not plan_id:
            plan_id = self.plan.id

        data = {
            "guest_email": "joe@example.com",
            "basket": reverse('basket-detail', args=[basket_id]),
            "shipping_address": {
                "first_name": "Joe",
                "last_name": "Schmoe",
                "line1": "234 5th Ave",
                "line4": "Manhattan",
                "postcode": "10001",
                "state": "NY",
                "country": reverse('country-detail', args=['US']),
                "phone_number": "+1 (717) 467-1111",
            },
            "billing_address": {
                "first_name": "Joe",
                "last_name": "Schmoe",
                "line1": "234 5th Ave",
                "line4": "Manhattan",
                "postcode": "10001",
                "state": "NY",
                "country": reverse('country-detail', args=['US']),
                "phone_number": "+1 (717) 467-1111",
            },
            "payment": {
                "wells-fargo": {
                    "enabled": True,
                    "account_number": account_number,
                    "financing_plan": plan_id,
                }
            }
        }
        url = reverse('api-checkout')
        resp = self.client.post(url, data, format='json')
        return resp


    def _fetch_payment_states(self):
        return self.client.get(reverse('api-payment'))
