from decimal import Decimal as D
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.reverse import reverse
from oscar.core.loading import get_model
from oscar.test import factories
import mock

from .base import BaseTest
from . import responses

Account = get_model('oscar_accounts', 'Account')


class CheckoutTest(BaseTest):
    """Full Integration Test of Checkout"""

    @mock.patch('soap.get_transport')
    def test_checkout_authd(self, get_transport):
        """Full checkout process using minimal api calls"""
        get_transport.return_value = self._build_transport_with_reply(responses.transaction_successful)

        user = User.objects.create_user(username='joe', password='schmoe')
        account = self._build_account('9999999999999999')
        account.primary_user = user
        account.save()

        self.client.login(username='joe', password='schmoe')

        # Should be successful
        basket_id = self._prepare_basket()
        resp = self._checkout(basket_id, account)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self._fetch_payment_states()
        self.assertEqual(resp.data['order_status'], 'Authorized')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['status'], 'Complete')
        self.assertEqual(resp.data['payment_method_states']['wells-fargo']['amount'], '10.00')


    @mock.patch('soap.get_transport')
    def test_checkout_anon(self, get_transport):
        """Full checkout process using minimal api calls"""
        get_transport.return_value = self._build_transport_with_reply(responses.transaction_successful)

        account = self._build_account('9999999999999999')

        # Put the account into the user's session
        session = self.client.session
        session['wfrs_accounts'] = [account.id]
        session.save()

        # Should be successful
        basket_id = self._prepare_basket()
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

        user = User.objects.create_user(username='joe', password='schmoe')
        account = self._build_account('9999999999999999')
        account.primary_user = user
        account.save()

        self.client.login(username='joe', password='schmoe')

        # Should be successful
        basket_id = self._prepare_basket()
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

        user1 = User.objects.create_user(username='joe', password='schmoe')
        User.objects.create_user(username='smitty', password='schmoe')

        account = self._build_account('9999999999999999')
        account.primary_user = user1
        account.save()

        # Client is not the user who owns the account
        self.client.login(username='smitty', password='schmoe')
        basket_id = self._prepare_basket()
        resp = self._checkout(basket_id, account)
        self.assertEqual(resp.status_code, status.HTTP_406_NOT_ACCEPTABLE)


    @mock.patch('soap.get_transport')
    def test_checkout_unauthorized_account2(self, get_transport):
        """Full checkout process using minimal api calls"""
        get_transport.return_value = self._build_transport_with_reply(responses.transaction_successful)

        user = User.objects.create_user(username='joe', password='schmoe')

        account = self._build_account('9999999999999999')
        account.primary_user = user
        account.save()

        # Client is anonymous
        basket_id = self._prepare_basket()
        resp = self._checkout(basket_id, account)
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
        res = self._add_to_basket(product.id)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self._get_basket()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        basket_id = res.data['id']
        return basket_id


    def _checkout(self, basket_id, account):
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
                }
            }
        }
        url = reverse('api-checkout')
        return self.client.post(url, data, format='json')


    def _fetch_payment_states(self):
        return self.client.get(reverse('api-payment'))
