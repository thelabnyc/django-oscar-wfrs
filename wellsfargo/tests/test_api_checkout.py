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
        self.client.login(username='joe', password='schmoe')

        product = self._create_product()

        res = self._get_basket()
        self.assertEqual(res.status_code, 200)
        basket_id = res.data['id']

        res = self._add_to_basket(product.id)
        self.assertEqual(res.status_code, 200)

        account = self._build_account('9999999999999999')
        account.primary_user = user
        account.save()

        resp = self._checkout(basket_id, account)
        self.assertEqual(resp.data['total_incl_tax'], '10.00')

        self.assertEqual(resp.data['shipping_method'], 'Free shipping')


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

    def _checkout(self, basket_id, account):
        data = {
            "guest_email": "herp@example.com",
            "basket": reverse('basket-detail', args=[basket_id]),
            "wfrs_source_account": account.pk,
            "shipping_address": {
                "first_name": "Joe",
                "last_name": "Schmoe",
                "line1": "234 5th Ave",
                "line4": "Manhattan",
                "postcode": "10001",
                "state": "NY",
                "country": reverse('country-detail', args=['US']),
                "phone_number": "+1 (717) 467-1111",
            }
        }
        url = reverse('wfrs-api-checkout')
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, 200)
        return res
