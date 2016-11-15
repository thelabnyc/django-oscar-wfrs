from datetime import datetime, timedelta
from decimal import Decimal as D
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.reverse import reverse
from oscar.core.loading import get_model
from oscar.test import factories
import mock

from .base import BaseTest
from . import responses
from ..models import FinancingPlan, FinancingPlanBenefit

Account = get_model('oscar_accounts', 'Account')
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
            proxy_class='wellsfargo.models.FinancingPlanBenefit',
            group_name='Financing is available')
        benefit.plans.add(self.plan)

        ConditionalOffer.objects.create(
            name='Financing is available',
            condition=condition,
            benefit=benefit,
            offer_type=ConditionalOffer.SITE,
            start_datetime=datetime.now() - timedelta(days=1),
            end_datetime=datetime.now() + timedelta(days=1))


    @mock.patch('soap.get_transport')
    def test_checkout_authd(self, get_transport):
        """Full checkout process using minimal api calls"""
        get_transport.return_value = self._build_transport_with_reply(responses.transaction_successful)

        account = self._build_account('9999999999999999')
        account.primary_user = self.joe
        account.save()

        self.client.login(username='joe', password='schmoe')

        # Should be successful
        basket_id = self._prepare_basket()
        self._check_available_plans()
        resp = self._checkout(basket_id, account)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self._fetch_payment_states()
        self.assertEqual(resp.data['order_status'], 'Authorized')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['status'], 'Complete')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['amount'], '10.00')


    @mock.patch('soap.get_transport')
    def test_checkout_trans_declined(self, get_transport):
        """Full checkout process using minimal api calls"""
        get_transport.return_value = self._build_transport_with_reply(responses.transaction_denied)

        account = self._build_account('9999999999999999')
        account.primary_user = self.joe
        account.save()

        self.client.login(username='joe', password='schmoe')

        # Should be successful
        basket_id = self._prepare_basket()
        self._check_available_plans()
        resp = self._checkout(basket_id, account)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self._fetch_payment_states()
        self.assertEqual(resp.data['order_status'], 'Payment Declined')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['status'], 'Declined')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['amount'], '10.00')


    @mock.patch('soap.get_transport')
    def test_checkout_unauthorized_account1(self, get_transport):
        """Full checkout process using minimal api calls"""
        get_transport.return_value = self._build_transport_with_reply(responses.transaction_successful)

        User.objects.create_user(username='smitty', password='schmoe')

        account = self._build_account('9999999999999999')
        account.primary_user = self.joe
        account.save()

        # Client is not the user who owns the account
        self.client.login(username='smitty', password='schmoe')
        basket_id = self._prepare_basket()
        self._check_available_plans()
        resp = self._checkout(basket_id, account)
        self.assertEqual(resp.status_code, status.HTTP_406_NOT_ACCEPTABLE)


    @mock.patch('soap.get_transport')
    def test_checkout_unauthorized_account2(self, get_transport):
        """Full checkout process using minimal api calls"""
        get_transport.return_value = self._build_transport_with_reply(responses.transaction_successful)

        account = self._build_account('9999999999999999')
        account.primary_user = self.joe
        account.save()

        basket_id = self._prepare_basket()

        # Client is anonymous
        url = reverse('wfrs-api-plan-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        resp = self._checkout(basket_id, account)
        self.assertEqual(resp.status_code, status.HTTP_406_NOT_ACCEPTABLE)


    @mock.patch('soap.get_transport')
    def test_checkout_bad_plan_number(self, get_transport):
        """Full checkout process using minimal api calls"""
        get_transport.return_value = self._build_transport_with_reply(responses.transaction_successful)

        account = self._build_account('9999999999999999')
        account.primary_user = self.joe
        account.save()

        self.client.login(username='joe', password='schmoe')

        # Should be successful
        basket_id = self._prepare_basket()
        self._check_available_plans()
        resp = self._checkout(basket_id, account, plan_id=self.plan.id + 1)
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


    def _checkout(self, basket_id, account, plan_id=None):
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
                    "account": account.id,
                    "financing_plan": plan_id,
                }
            }
        }
        url = reverse('api-checkout')
        resp = self.client.post(url, data, format='json')
        return resp


    def _fetch_payment_states(self):
        return self.client.get(reverse('api-payment'))
