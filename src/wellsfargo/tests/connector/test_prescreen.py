from decimal import Decimal
from wellsfargo.connector.prescreen import PrescreenAPIClient
from wellsfargo.models import PreQualificationRequest
from wellsfargo.tests.base import BaseTest
# import requests_mock



class PrescreenAPIClientTest(BaseTest):

    # @requests_mock.Mocker()
    def test_prequal_success(self):
        # self.mock_get_api_token_request(rmock)

        # def match_submit_transaction(request):
        #     # Check auth header
        #     self.assertTrue(request.headers['Authorization'].startswith('Bearer '))
        #     # Check data in body
        #     data = json.loads(request.body)
        #     self.assertEqual(data, {
        #         "main_applicant": {
        #             "address": {
        #                 "address_line_1": "",
        #                 "city": "",
        #                 "state_code": "",
        #                 "postal_code": "",
        #             },
        #             "first_name": "",
        #             "last_name": "",
        #             "email": "",
        #         },
        #         "merchant_number": "",
        #         "transaction_code": "MAH",
        #         "entry_point": "",
        #     })
        #     return True

        # rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/prequalifications',
        #     additional_matcher=match_request,
        #     json={
        #         "access_token": "16a05f65dd41569af67dbdca7ea4da4d",
        #         "scope": "",
        #         "token_type": "Bearer",
        #         "expires_in": 79900,
        #     },
        # )

        request = PreQualificationRequest()
        request.email = 'joe@example.com'
        request.first_name = 'Joe'
        request.last_name = 'Schmoe'
        request.line1 = '123 Evergreen Terrace'
        request.city = 'Springfield'
        request.state = 'NY'
        request.postcode = '10001'
        request.phone = '+1 (212) 209-1333'
        request.save()

        resp = PrescreenAPIClient().check_prescreen_status(request)

        self.assertEqual(resp.request, request)
        self.assertEqual(resp.status, 'A')
        self.assertEqual(resp.is_approved, True)
        self.assertEqual(resp.message, 'approved')
        self.assertEqual(resp.offer_indicator, 'F1')
        self.assertEqual(resp.credit_limit, Decimal('8500.00'))
        self.assertEqual(resp.response_id, '000005EP')
        self.assertEqual(resp.application_url, 'https://localhost/ipscr.do?id=u64RVNDAAAAICbmCjLaoQIJNSOJhojOkEssokkO3WvGBqdOxl_4BfA.')
        self.assertEqual(resp.customer_response, '')
