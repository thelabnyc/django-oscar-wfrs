from rest_framework import status
from rest_framework.reverse import reverse
from .base import BaseTest
from . import responses
import mock


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
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['url'].endswith('/apply/us-individual/'))


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
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_number'], '9999999999999999')
        self.assertEqual(response.data['credit_limit'], '7500.00')
        self.assertEqual(response.data['balance'], '0.00')
        self.assertEqual(response.data['open_to_buy'], '7500.00')

    @mock.patch('soap.get_transport')
    def test_submit_authd(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_successful)

        self.client.login(username='joe', password='schmoe')

        url = reverse(self.view_name)
        data = self.build_valid_request()
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_number'], '9999999999999999')
        self.assertEqual(response.data['credit_limit'], '7500.00')
        self.assertEqual(response.data['balance'], '0.00')
        self.assertEqual(response.data['open_to_buy'], '7500.00')

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
