from rest_framework import status
from rest_framework.reverse import reverse
from wellsfargo.tests.base import BaseTest
import requests_mock


class CreditLineInquiryTest(BaseTest):
    @requests_mock.Mocker()
    def test_inquiry_successful(self, rmock):
        self.mock_get_api_token_request(rmock)
        self.mock_successful_joint_account_inquiry(rmock)

        url = reverse("wfrs-api-acct-inquiry")
        data = {"account_number": "2222222222222222"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["account_number"], "2222222222222222")
        self.assertEqual(response.data["main_applicant_full_name"], "Schmoe, Joe")
        self.assertEqual(response.data["joint_applicant_full_name"], "Schmoe, Karen")
        self.assertEqual(
            response.data["main_applicant_address"],
            {
                "address_line_1": "123 FIRST STREET",
                "address_line_2": "APT  456",
                "city": "DES MOINES",
                "state_code": "IA",
                "postal_code": "50322",
            },
        )
        self.assertEqual(
            response.data["joint_applicant_address"],
            {
                "address_line_1": "19 ARLEN RD APT J",
                "address_line_2": "",
                "city": "BALTIMORE",
                "state_code": "MD",
                "postal_code": "21236-5152",
            },
        )
        self.assertEqual(response.data["credit_limit"], "18000.00")
        self.assertEqual(response.data["available_credit"], "14455.00")

    @requests_mock.Mocker()
    def test_inquiry_failed(self, rmock):
        self.mock_get_api_token_request(rmock)
        self.mock_failed_individual_account_inquiry(rmock)

        url = reverse("wfrs-api-acct-inquiry")
        data = {"account_number": "2222222222222222"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["account_number"],
            ["'account_number' cannot have fewer than 15 character(s)."],
        )

    @requests_mock.Mocker()
    def test_inquiry_still_pending(self, rmock):
        self.mock_get_api_token_request(rmock)
        self.mock_pending_individual_account_inquiry(rmock)

        url = reverse("wfrs-api-acct-inquiry")
        data = {"account_number": "2222222222222222"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, None)
