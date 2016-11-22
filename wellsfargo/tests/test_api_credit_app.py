from rest_framework import status
from rest_framework.reverse import reverse
from oscar.core.loading import get_model
import mock

from .base import BaseTest
from . import responses

Account = get_model('oscar_accounts', 'Account')


class CreditApplicationSelectorTest(BaseTest):
    def test_us_i(self):
        self.client.login(username='joe', password='schmoe')
        url = reverse('wfrs-api-apply-select')
        data = {
            'region': 'US',
            'app_type': 'I'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['url'].endswith('/apply/us-individual/'))

    def test_us_j(self):
        self.client.login(username='joe', password='schmoe')
        url = reverse('wfrs-api-apply-select')
        data = {
            'region': 'US',
            'app_type': 'J'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['url'].endswith('/apply/us-joint/'))

    def test_ca_i(self):
        self.client.login(username='joe', password='schmoe')
        url = reverse('wfrs-api-apply-select')
        data = {
            'region': 'CA',
            'app_type': 'I'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['url'].endswith('/apply/ca-individual/'))

    def test_ca_j(self):
        self.client.login(username='joe', password='schmoe')
        url = reverse('wfrs-api-apply-select')
        data = {
            'region': 'CA',
            'app_type': 'J'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['url'].endswith('/apply/ca-joint/'))

    def test_mx_i(self):
        self.client.login(username='joe', password='schmoe')
        url = reverse('wfrs-api-apply-select')
        data = {
            'region': 'MX',
            'app_type': 'I'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous(self):
        url = reverse('wfrs-api-apply-select')
        data = {
            'region': 'US',
            'app_type': 'I'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class USIndivCreditApplicationTest(BaseTest):
    view_name = 'wfrs-api-apply-us-individual'

    def build_valid_request(self):
        return {
            'region': 'US',
            'app_type': 'I',
            'language': 'E',
            'purchase_price': 2000,
            'main_ssn': '999999991',
            'main_first_name': 'Joe',
            'main_last_name': 'Schmoe',
            'main_date_of_birth': '1990-01-01',
            'email': 'foo@example.com',
            'main_address_line1': '123 Evergreen Terrace',
            'main_address_city': 'Springfield',
            'main_address_state': 'NY',
            'main_address_postcode': '10001',
            'main_annual_income': '100000',
            'main_home_phone': '5555555555',
            'main_employer_phone': '5555555555',
        }

    def build_invalid_request(self):
        return {
            'region': 'US',
            'app_type': 'I',
            'language': 'E',
            'main_ssn': '999999991',
            'main_first_name': 'Joe',
            'main_last_name': 'Schmoe',
            'main_date_of_birth': '',
            'email': 'foo@example.com',
            'main_address_line1': '123 Evergreen Terrace',
            'main_address_city': 'Springfield',
            'main_address_state': 'NY',
            'main_address_postcode': '10001',
            'main_annual_income': '100000',
            'main_home_phone': '5555555555',
            'main_employer_phone': '5555555555',
        }

    @mock.patch('soap.get_transport')
    def test_submit_anon(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_successful)

        url = reverse(self.view_name)
        data = self.build_valid_request()
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('soap.get_transport')
    def test_submit_authd(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_successful)

        self.client.login(username='joe', password='schmoe')

        url = reverse(self.view_name)
        data = self.build_valid_request()
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['id'])
        self.assertIsNotNone(response.data['url'])
        self.assertEqual(response.data['name'], 'Joe Schmoe – xxxxxxxxxxxx9999')
        self.assertIsNone(response.data['description'])
        self.assertEqual(response.data['code'], '9999999999999999')
        self.assertEqual(response.data['status'], 'Open')
        self.assertEqual(response.data['credit_limit'], '7500.00')
        self.assertEqual(response.data['balance'], '0.00')
        self.assertEqual(response.data['locale'], 'en_US')
        self.assertEqual(response.data['account_number'], '9999999999999999')

    def test_submit_invalid(self):
        self.client.login(username='joe', password='schmoe')

        url = reverse(self.view_name)
        data = self.build_invalid_request()
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('soap.get_transport')
    def test_submit_denied(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_denied)

        self.client.login(username='joe', password='schmoe')

        url = reverse(self.view_name)
        data = self.build_valid_request()
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Credit Application was denied by Wells Fargo')

    def test_manual_add(self):
        self.client.login(username='joe', password='schmoe')

        url = reverse('wfrs-api-account-list')
        data = {
            'account_number': '1111111111111111',
            'billing_address': {
                'title': 'Ms',
                'first_name': 'Jill',
                'last_name': 'Schmoe',
                'line1': '111 Wall St',
                'line4': 'New York',
                'state': 'NY',
                'postcode': '10001',
                'country': '/api/countries/US/',
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['id'])
        self.assertIsNotNone(response.data['url'])
        self.assertEqual(response.data['name'], 'Ms Jill Schmoe – xxxxxxxxxxxx1111')
        self.assertIsNone(response.data['description'])
        self.assertEqual(response.data['code'], '1111111111111111')
        self.assertEqual(response.data['status'], 'Open')
        self.assertIsNone(response.data['credit_limit'])
        self.assertEqual(response.data['balance'], '0.00')
        self.assertEqual(response.data['locale'], 'en_US')
        self.assertEqual(response.data['account_number'], '1111111111111111')
        self.assertEqual(response.data['billing_address']['title'], 'Ms')
        self.assertEqual(response.data['billing_address']['first_name'], 'Jill')
        self.assertEqual(response.data['billing_address']['last_name'], 'Schmoe')
        self.assertEqual(response.data['billing_address']['line1'], '111 Wall St')
        self.assertEqual(response.data['billing_address']['line2'], '')
        self.assertEqual(response.data['billing_address']['line4'], 'New York')
        self.assertEqual(response.data['billing_address']['state'], 'NY')
        self.assertEqual(response.data['billing_address']['postcode'], '10001')
        self.assertEqual(response.data['billing_address']['country'], 'http://testserver/api/countries/US/')

    def test_manual_add_without_billing_address(self):
        self.client.login(username='joe', password='schmoe')

        url = reverse('wfrs-api-account-list')
        data = {
            "account_number": "1111111111111111",
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['id'])
        self.assertIsNotNone(response.data['url'])
        self.assertEqual(response.data['name'], 'xxxxxxxxxxxx1111')
        self.assertIsNone(response.data['description'])
        self.assertEqual(response.data['code'], '1111111111111111')
        self.assertEqual(response.data['status'], 'Open')
        self.assertIsNone(response.data['credit_limit'])
        self.assertEqual(response.data['balance'], '0.00')
        self.assertEqual(response.data['locale'], 'en_US')
        self.assertEqual(response.data['account_number'], '1111111111111111')
        self.assertIsNone(response.data['billing_address'])
