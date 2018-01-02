from rest_framework import status
from rest_framework.reverse import reverse
from wellsfargo.models import USCreditApp
from wellsfargo.tests.base import BaseTest
from wellsfargo.tests import responses
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
            'main_home_phone': '+1 (212) 209-1333',
            'main_employer_phone': '+1 (212) 209-1333',
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

        app = USCreditApp.objects.first()

        self.assertEqual(app.user, None)
        self.assertEqual(app.submitting_user, None)

        # Basic Application Data
        self.assertEqual(app.region, 'US')
        self.assertEqual(app.app_type, 'I')
        self.assertEqual(app.language, 'E')
        self.assertEqual(app.purchase_price, 2000)
        self.assertEqual(app.main_ssn, 'xxx-xx-9991')  # Model should only contain masked SSN, not full SSN.
        self.assertEqual(app.main_first_name, 'Joe')
        self.assertEqual(app.main_last_name, 'Schmoe')
        self.assertEqual(app.main_date_of_birth, None)  # Model should not store Date of Birth
        self.assertEqual(app.email, 'foo@example.com')
        self.assertEqual(app.main_address_line1, '123 Evergreen Terrace')
        self.assertEqual(app.main_address_city, 'Springfield')
        self.assertEqual(app.main_address_state, 'NY')
        self.assertEqual(app.main_address_postcode, '10001')
        self.assertEqual(app.main_annual_income, 100000)
        self.assertEqual(app.main_home_phone.as_e164, '+12122091333')
        self.assertEqual(app.main_employer_phone.as_e164, '+12122091333')

        # Computed properties
        self.assertEqual(app.locale, 'en_US')
        self.assertEqual(app.is_joint, False)
        self.assertEqual(app.full_name, 'Joe Schmoe')

        # Model should store last 4 digits of resulting account number
        self.assertEqual(app.last4_account_number, '9999')
        self.assertEqual(app.masked_account_number, 'xxxxxxxxxxxx9999')
        self.assertEqual(app.account_number, 'xxxxxxxxxxxx9999')


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

        app = USCreditApp.objects.first()

        self.assertEqual(app.user, self.joe)
        self.assertEqual(app.submitting_user, self.joe)

        # Basic Application Data
        self.assertEqual(app.region, 'US')
        self.assertEqual(app.app_type, 'I')
        self.assertEqual(app.language, 'E')
        self.assertEqual(app.purchase_price, 2000)
        self.assertEqual(app.main_ssn, 'xxx-xx-9991')  # Model should only contain masked SSN, not full SSN.
        self.assertEqual(app.main_first_name, 'Joe')
        self.assertEqual(app.main_last_name, 'Schmoe')
        self.assertEqual(app.main_date_of_birth, None)  # Model should not store Date of Birth
        self.assertEqual(app.email, 'foo@example.com')
        self.assertEqual(app.main_address_line1, '123 Evergreen Terrace')
        self.assertEqual(app.main_address_city, 'Springfield')
        self.assertEqual(app.main_address_state, 'NY')
        self.assertEqual(app.main_address_postcode, '10001')
        self.assertEqual(app.main_annual_income, 100000)
        self.assertEqual(app.main_home_phone.as_e164, '+12122091333')
        self.assertEqual(app.main_employer_phone.as_e164, '+12122091333')

        # Computed properties
        self.assertEqual(app.locale, 'en_US')
        self.assertEqual(app.is_joint, False)
        self.assertEqual(app.full_name, 'Joe Schmoe')

        # Model should store last 4 digits of resulting account number
        self.assertEqual(app.last4_account_number, '9999')
        self.assertEqual(app.masked_account_number, 'xxxxxxxxxxxx9999')
        self.assertEqual(app.account_number, 'xxxxxxxxxxxx9999')


    def test_submit_invalid_dob(self):
        self.client.login(username='joe', password='schmoe')

        url = reverse(self.view_name)
        data = self.build_valid_request()
        data['main_date_of_birth'] = ''  # Make request invalid due to missing DOB
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('main_date_of_birth' in response.data)
        self.assertEqual(len(response.data['main_date_of_birth']), 1)


    @mock.patch('soap.get_transport')
    def test_submit_invalid_ssn(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_invalid_ssn)

        self.client.login(username='joe', password='schmoe')

        url = reverse(self.view_name)
        data = self.build_valid_request()
        data['main_ssn'] = '999999999'  # Make request invalid due to invalid SSN
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('non_field_errors' in response.data)
        self.assertEqual(len(response.data['non_field_errors']), 1)
        self.assertEqual(response.data['non_field_errors'][0], 'BAD SOCIAL SECURITY NUMBER')


    @mock.patch('soap.get_transport')
    def test_submit_denied(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_denied)

        self.client.login(username='joe', password='schmoe')

        url = reverse(self.view_name)
        data = self.build_valid_request()
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Credit Application was denied by Wells Fargo')


    @mock.patch('soap.get_transport')
    def test_submit_pending(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_pending)

        self.client.login(username='joe', password='schmoe')

        url = reverse(self.view_name)
        data = self.build_valid_request()
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Credit Application approval is pending')
