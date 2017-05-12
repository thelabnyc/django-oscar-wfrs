from rest_framework import status
from rest_framework.reverse import reverse
from wellsfargo.tests.base import BaseTest
from wellsfargo.tests import responses
import mock


class CreditLineInquiryTest(BaseTest):

    @mock.patch('soap.get_transport')
    def test_inquiry_successful(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.inquiry_successful)

        url = reverse('wfrs-api-acct-inquiry')
        data = {
            'account_number': '9999999999999991'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_number'], '9999999999999991')
        self.assertEqual(response.data['status'], 'I0')
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['middle_initial'], 'Q')
        self.assertEqual(response.data['last_name'], 'Smith')
        self.assertEqual(response.data['phone_number'], '+15559998888')
        self.assertEqual(response.data['address'], '123 First Street')
        self.assertEqual(response.data['credit_limit'], '5000.00')
        self.assertEqual(response.data['balance'], '0.00')
        self.assertEqual(response.data['open_to_buy'], '5000.00')
        self.assertEqual(response.data['last_payment_date'], None)
        self.assertEqual(response.data['last_payment_amount'], '0.00')
        self.assertEqual(response.data['payment_due_date'], None)
        self.assertEqual(response.data['payment_due_amount'], '0.00')



    @mock.patch('soap.get_transport')
    def test_inquiry_failed(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.inquiry_failed)

        url = reverse('wfrs-api-acct-inquiry')
        data = {
            'account_number': '9999999999999991'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['account_number'], ['DEMO INVALID ACCOUNT'])
