from rest_framework import status
from rest_framework.reverse import reverse
from wellsfargo.tests.base import BaseTest
from wellsfargo.tests import responses
import mock


class PreQualificationRequestTest(BaseTest):

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
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'A')
        self.assertEqual(response.data['is_approved'], True)
        self.assertEqual(response.data['message'], 'approved')
        self.assertEqual(response.data['credit_limit'], '8500.00')
        self.assertEqual(response.data['customer_response'], '')


    @mock.patch('soap.get_transport')
    def test_prequal_failed(self, get_transport):
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
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'], ['Phone is blank or invalid.'])
