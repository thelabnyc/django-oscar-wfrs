from rest_framework import status
from rest_framework.reverse import reverse
from wellsfargo.tests.base import BaseTest
from wellsfargo.tests import responses
import mock
from wellsfargo.models import PreQualificationRequest


class PreQualificationRequestTest(BaseTest):
    def setUp(self):
        super().setUp()
        # Test IPAddress to use
        self.ip_address = '127.0.0.1'

    @mock.patch('soap.get_transport')
    def test_prequal_successful(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.prequal_successful)

        url = reverse('wfrs-api-prequal')
        data = {
            'first_name': 'Joe',
            'last_name': 'Schmoe',
            'line1': '123 Evergreen Terrace',
            'city': 'Springfield',
            'state': 'NY',
            'postcode': '10001',
            'phone': '+1 (212) 209-1333',
        }
        response = self.client.post(url, data, format='json', REMOTE_ADDR=self.ip_address)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'A')
        self.assertEqual(response.data['is_approved'], True)
        self.assertEqual(response.data['message'], 'approved')
        self.assertEqual(response.data['credit_limit'], '8500.00')
        self.assertEqual(response.data['customer_response'], '')

        get_transport.return_value = self._build_transport_with_reply(responses.otb_successful)
        url = "{}?A=41".format(reverse('wfrs-api-prequal-app-complete'))
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertInHTML('<h1>Your Wells Fargo application was approved.</h1>', response.content.decode())
        self.assertInHTML('<p>Your account number is 9999999999999999.</p>', response.content.decode())
        self.assertInHTML('<p>Your credit limit is 9000.00.</p>', response.content.decode())

        # Check if IPAddress was stored
        prequal_request = PreQualificationRequest.objects.first()
        self.assertEqual(prequal_request.ip_address, self.ip_address)


    @mock.patch('soap.get_transport')
    def test_prequal_failed_prescreen(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.prequal_failed)

        url = reverse('wfrs-api-prequal')
        data = {
            'first_name': 'Joe',
            'last_name': 'Schmoe',
            'line1': '123 Evergreen Terrace',
            'city': 'Springfield',
            'state': 'NY',
            'postcode': '10001',
            'phone': '+1 (212) 209-1333',
        }
        response = self.client.post(url, data, format='json', REMOTE_ADDR=self.ip_address)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'], ['Phone is blank or invalid.'])

        # Check if IPAddress was stored
        prequal_request = PreQualificationRequest.objects.first()
        self.assertEqual(prequal_request.ip_address, self.ip_address)


    @mock.patch('soap.get_transport')
    def test_prequal_failed_application(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.prequal_successful)

        url = reverse('wfrs-api-prequal')
        data = {
            'first_name': 'Joe',
            'last_name': 'Schmoe',
            'line1': '123 Evergreen Terrace',
            'city': 'Springfield',
            'state': 'NY',
            'postcode': '10001',
            'phone': '+1 (212) 209-1333',
        }
        response = self.client.post(url, data, format='json', REMOTE_ADDR=self.ip_address)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'A')
        self.assertEqual(response.data['is_approved'], True)
        self.assertEqual(response.data['message'], 'approved')
        self.assertEqual(response.data['credit_limit'], '8500.00')
        self.assertEqual(response.data['customer_response'], '')

        get_transport.return_value = self._build_transport_with_reply(responses.otb_denied)
        url = reverse('wfrs-api-prequal-app-complete')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertInHTML('<h1>Your Wells Fargo application was not approved.</h1>', response.content.decode())

        # Check if IPAddress was stored
        prequal_request = PreQualificationRequest.objects.first()
        self.assertEqual(prequal_request.ip_address, self.ip_address)


    @mock.patch('soap.get_transport')
    def test_prequal_failed_error(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.prequal_successful)

        url = reverse('wfrs-api-prequal')
        data = {
            'first_name': 'Joe',
            'last_name': 'Schmoe',
            'line1': '123 Evergreen Terrace',
            'city': 'Springfield',
            'state': 'NY',
            'postcode': '10001',
            'phone': '+1 (212) 209-1333',
        }
        response = self.client.post(url, data, format='json', REMOTE_ADDR=self.ip_address)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'A')
        self.assertEqual(response.data['is_approved'], True)
        self.assertEqual(response.data['message'], 'approved')
        self.assertEqual(response.data['credit_limit'], '8500.00')
        self.assertEqual(response.data['customer_response'], '')

        get_transport.return_value = self._build_transport_with_reply(responses.otb_error)
        url = "{}?A=41".format(reverse('wfrs-api-prequal-app-complete'))
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertInHTML('<h1>Your Wells Fargo application was not approved.</h1>', response.content.decode())

        # Check if IPAddress was stored
        prequal_request = PreQualificationRequest.objects.first()
        self.assertEqual(prequal_request.ip_address, self.ip_address)


    def test_sdk_prequal_response(self):
        url = reverse('wfrs-api-prequal-sdk-response')
        data = {
            'first_name': 'Joe',
            'last_name': 'Schmoe',
            'line1': '123 Evergreen Terrace',
            'city': 'Springfield',
            'state': 'NY',
            'postcode': '10001',
            'status': 'A',
            'credit_limit': '7500.00',
            'response_id': 'ABC123',
        }
        response = self.client.post(url, data, format='json', REMOTE_ADDR=self.ip_address)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'A')
        self.assertEqual(response.data['is_approved'], True)
        self.assertEqual(response.data['message'], '')
        self.assertEqual(response.data['credit_limit'], '7500.00')
        self.assertEqual(response.data['customer_response'], '')

        url = reverse('wfrs-api-prequal-customer-response')
        data = {
            'customer_response': 'SDKPRESENTED',
        }
        response = self.client.post(url, data, format='json', REMOTE_ADDR=self.ip_address)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'A')
        self.assertEqual(response.data['is_approved'], True)
        self.assertEqual(response.data['message'], '')
        self.assertEqual(response.data['credit_limit'], '7500.00')
        self.assertEqual(response.data['customer_response'], 'SDKPRESENTED')

        # Check if IPAddress was stored
        prequal_request = PreQualificationRequest.objects.first()
        self.assertEqual(prequal_request.ip_address, self.ip_address)
