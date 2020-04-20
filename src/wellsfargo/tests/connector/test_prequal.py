from decimal import Decimal
from django.core.exceptions import ValidationError
from wellsfargo.connector.prequal import PrequalAPIClient
from wellsfargo.models import PreQualificationRequest
from wellsfargo.tests.base import BaseTest
import requests_mock
import json



class PrequalAPIClientTest(BaseTest):

    @requests_mock.Mocker()
    def test_prequal_success(self, rmock):
        self.mock_get_api_token_request(rmock)

        def match_request(request):
            # Check auth header
            self.assertTrue(request.headers['Authorization'].startswith('Bearer '))
            # Check data in body
            data = json.loads(request.body)
            self.assertEqual(data, {
                "merchant_number": "1111111111111111",
                "transaction_code": "MAH",
                "main_applicant": {
                    "first_name": "Demo",
                    "last_name": "Tester",
                    "phone_number": "2122091333",
                    "email": "demo@wellsfargo.com",
                    "address": {
                        "address_line_1": "800 Walnut St",
                        "city": "Des Moines",
                        "state_code": "IA",
                        "postal_code": "50309",
                    },
                },
                "entry_point": "WEB",
            })
            return True

        self.mock_successful_prescreen_request(rmock, additional_matcher=match_request)

        request = PreQualificationRequest()
        request.email = 'demo@wellsfargo.com'
        request.first_name = 'Demo'
        request.last_name = 'Tester'
        request.line1 = '800 Walnut St'
        request.city = 'Des Moines'
        request.state = 'IA'
        request.postcode = '50309'
        request.phone = '+1 (212) 209-1333'
        request.save()

        resp = PrequalAPIClient().check_prescreen_status(request)

        self.assertEqual(resp.request, request)
        self.assertEqual(resp.status, 'A')
        self.assertEqual(resp.is_approved, True)
        self.assertEqual(resp.message, 'APPROVED')
        self.assertEqual(resp.offer_indicator, '')
        self.assertEqual(resp.credit_limit, Decimal('8500.00'))
        self.assertEqual(resp.response_id, '000005EP')
        self.assertEqual(resp.application_url, '')
        self.assertEqual(resp.customer_response, '')


    @requests_mock.Mocker()
    def test_prequal_denied(self, rmock):
        self.mock_get_api_token_request(rmock)
        self.mock_denied_prescreen_request(rmock)

        request = PreQualificationRequest()
        request.email = 'demo@wellsfargo.com'
        request.first_name = 'Bruce'
        request.last_name = 'Smith'
        request.line1 = '304 Buckels'
        request.city = 'Houston'
        request.state = 'PA'
        request.postcode = '15342'
        request.phone = '+1 (212) 209-1333'
        request.save()

        resp = PrequalAPIClient().check_prescreen_status(request)

        self.assertEqual(resp.request, request)
        self.assertEqual(resp.status, 'D')
        self.assertEqual(resp.is_approved, False)
        self.assertEqual(resp.message, 'DENIED')
        self.assertEqual(resp.offer_indicator, '')
        self.assertEqual(resp.credit_limit, Decimal('0.00'))
        self.assertEqual(resp.response_id, '')
        self.assertEqual(resp.application_url, '')
        self.assertEqual(resp.customer_response, '')


    @requests_mock.Mocker()
    def test_prequal_failure(self, rmock):
        self.mock_get_api_token_request(rmock)
        self.mock_invalid_prescreen_request(rmock)

        request = PreQualificationRequest()
        request.first_name = 'Joe'
        request.last_name = 'Schmoe'
        request.line1 = '123 Evergreen Terrace'
        request.city = 'Springfield'
        request.state = 'NY'
        request.postcode = '10001'
        request.phone = '+1 (212) 209-1333'
        request.save()

        with self.assertRaises(ValidationError):
            PrequalAPIClient().check_prescreen_status(request)
