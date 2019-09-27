from rest_framework import status
from rest_framework.reverse import reverse
from wellsfargo.tests.base import BaseTest
from wellsfargo.tests import responses
from unittest import mock
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


    def test_sdk_resume_prequal(self):
        # Set-up a prequal response
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

        # Hit the resume view
        prequal_request = PreQualificationRequest.objects.first()
        url = prequal_request.get_resume_offer_url(next_url='/my-redirect/')
        response = self.client.get(url)
        self.assertRedirects(response, '/my-redirect/', fetch_redirect_response=False)

        # Resume should work with a full next_url
        hostname = "testsite.com"
        prequal_request = PreQualificationRequest.objects.first()
        url = prequal_request.get_resume_offer_url(next_url="http://{hostname}/my-redirect/".format(hostname=hostname))
        response = self.client.get(url, SERVER_NAME=hostname)
        self.assertRedirects(response, "http://{hostname}/my-redirect/".format(hostname=hostname), fetch_redirect_response=False)

        # Full next_url to another site fails
        prequal_request = PreQualificationRequest.objects.first()
        url = prequal_request.get_resume_offer_url(next_url='http://not-my-site.com/my-redirect/')
        response = self.client.get(url)
        self.assertRedirects(response, '/', fetch_redirect_response=False)

        # Fetch the response data
        url = reverse('wfrs-api-prequal-sdk-response')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['request']['first_name'], 'Joe')
        self.assertEqual(response.data['request']['last_name'], 'Schmoe')
        self.assertEqual(response.data['request']['line1'], '123 Evergreen Terrace')
        self.assertEqual(response.data['request']['line2'], None)
        self.assertEqual(response.data['request']['city'], 'Springfield')
        self.assertEqual(response.data['request']['state'], 'NY')
        self.assertEqual(response.data['request']['postcode'], '10001')
        self.assertEqual(response.data['status'], 'A')
        self.assertEqual(response.data['is_approved'], True)
        self.assertEqual(response.data['message'], '')
        self.assertEqual(response.data['credit_limit'], '7500.00')
        self.assertEqual(response.data['customer_response'], 'SDKPRESENTED')
        self.assertEqual(response.data['full_application_url'], '&mn=1111111111')
        self.assertEqual(response.data['offer_indicator'], '')
        self.assertEqual(response.data['response_id'], 'ABC123')
        self.assertEqual(response.data['sdk_application_result'], None)
