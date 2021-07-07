from rest_framework import status
from rest_framework.reverse import reverse
from wellsfargo.models import CreditApplication
from wellsfargo.tests.base import BaseTest
import requests_mock


class CreditApplicationTest(BaseTest):
    view_name = "wfrs-api-apply"

    def build_valid_request(self):
        return {
            "main_applicant": {
                "address": {
                    "address_line_1": "123 Evergreen Terrace",
                    "city": "Springfield",
                    "postal_code": "10001",
                    "state_code": "NY",
                },
                "annual_income": 100000,
                "date_of_birth": "1991-01-01",
                "email_address": "foo@example.com",
                "employer_name": "self",
                "first_name": "Joe",
                "home_phone": "+1 (212) 209-1333",
                "housing_status": "Rent",
                "last_name": "Schmoe",
                "mobile_phone": "+1 (212) 209-1333",
                "ssn": "999999991",
                "work_phone": "+1 (212) 209-1333",
            },
            "merchant_number": "1111111111111111",
            "requested_credit_limit": 2000,
        }

    @requests_mock.Mocker()
    def test_submit_anon(self, rmock):
        self.mock_get_api_token_request(rmock)
        self.mock_successful_credit_app_request(rmock)

        url = reverse(self.view_name)
        data = self.build_valid_request()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["account_number"], "9999999999999999")
        self.assertEqual(response.data["credit_limit"], "7500.00")
        self.assertEqual(response.data["available_credit"], "7500.00")

        app = CreditApplication.objects.first()

        self.assertEqual(app.user, None)
        self.assertEqual(app.submitting_user, None)

        # Basic Application Data
        self.assertEqual(app.requested_credit_limit, 2000)
        self.assertEqual(
            app.main_applicant.ssn, "xxx-xx-9991"
        )  # Model should only contain masked SSN, not full SSN.
        self.assertEqual(app.main_applicant.first_name, "Joe")
        self.assertEqual(app.main_applicant.last_name, "Schmoe")
        self.assertEqual(
            app.main_applicant.date_of_birth, None
        )  # Model should not store Date of Birth
        self.assertEqual(app.main_applicant.email_address, "foo@example.com")
        self.assertEqual(app.main_applicant.home_phone.as_e164, "+12122091333")
        self.assertEqual(app.main_applicant.mobile_phone.as_e164, "+12122091333")
        self.assertEqual(app.main_applicant.work_phone.as_e164, "+12122091333")
        self.assertEqual(
            app.main_applicant.address.address_line_1, "123 Evergreen Terrace"
        )
        self.assertEqual(app.main_applicant.address.address_line_2, "")
        self.assertEqual(app.main_applicant.address.city, "Springfield")
        self.assertEqual(app.main_applicant.address.state_code, "NY")
        self.assertEqual(app.main_applicant.address.postal_code, "10001")
        self.assertEqual(app.main_applicant.annual_income, 100000)
        self.assertEqual(app.joint_applicant, None)

        # Computed properties
        self.assertEqual(app.full_name, "Joe Schmoe")

        # Account numbers
        self.assertEqual(app.last4_account_number, "9999")
        self.assertEqual(app.masked_account_number, "xxxxxxxxxxxx9999")
        self.assertEqual(app.account_number, "9999999999999999")

        app.purge_encrypted_account_number()

        self.assertEqual(app.last4_account_number, "9999")
        self.assertEqual(app.masked_account_number, "xxxxxxxxxxxx9999")
        self.assertEqual(app.account_number, "xxxxxxxxxxxx9999")

    @requests_mock.Mocker()
    def test_submit_authd(self, rmock):
        self.mock_get_api_token_request(rmock)
        self.mock_successful_credit_app_request(rmock)

        self.client.login(username="joe", password="schmoe")

        url = reverse(self.view_name)
        data = self.build_valid_request()
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["account_number"], "9999999999999999")
        self.assertEqual(response.data["credit_limit"], "7500.00")
        self.assertEqual(response.data["available_credit"], "7500.00")

        app = CreditApplication.objects.first()

        self.assertEqual(app.user, self.joe)
        self.assertEqual(app.submitting_user, self.joe)

        # Basic Application Data
        self.assertEqual(app.requested_credit_limit, 2000)
        self.assertEqual(
            app.main_applicant.ssn, "xxx-xx-9991"
        )  # Model should only contain masked SSN, not full SSN.
        self.assertEqual(app.main_applicant.first_name, "Joe")
        self.assertEqual(app.main_applicant.last_name, "Schmoe")
        self.assertEqual(
            app.main_applicant.date_of_birth, None
        )  # Model should not store Date of Birth
        self.assertEqual(app.main_applicant.email_address, "foo@example.com")
        self.assertEqual(app.main_applicant.home_phone.as_e164, "+12122091333")
        self.assertEqual(app.main_applicant.mobile_phone.as_e164, "+12122091333")
        self.assertEqual(app.main_applicant.work_phone.as_e164, "+12122091333")
        self.assertEqual(
            app.main_applicant.address.address_line_1, "123 Evergreen Terrace"
        )
        self.assertEqual(app.main_applicant.address.address_line_2, "")
        self.assertEqual(app.main_applicant.address.city, "Springfield")
        self.assertEqual(app.main_applicant.address.state_code, "NY")
        self.assertEqual(app.main_applicant.address.postal_code, "10001")
        self.assertEqual(app.main_applicant.annual_income, 100000)
        self.assertEqual(app.joint_applicant, None)

        # Computed properties
        self.assertEqual(app.full_name, "Joe Schmoe")

        # Account numbers
        self.assertEqual(app.last4_account_number, "9999")
        self.assertEqual(app.masked_account_number, "xxxxxxxxxxxx9999")
        self.assertEqual(app.account_number, "9999999999999999")

        app.purge_encrypted_account_number()

        self.assertEqual(app.last4_account_number, "9999")
        self.assertEqual(app.masked_account_number, "xxxxxxxxxxxx9999")
        self.assertEqual(app.account_number, "xxxxxxxxxxxx9999")

    @requests_mock.Mocker()
    def test_submit_invalid_dob(self, rmock):
        self.client.login(username="joe", password="schmoe")

        url = reverse(self.view_name)
        data = self.build_valid_request()
        data["main_applicant"][
            "date_of_birth"
        ] = ""  # Make request invalid due to missing DOB
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("date_of_birth" in response.data["main_applicant"])
        self.assertEqual(len(response.data["main_applicant"]["date_of_birth"]), 1)

    @requests_mock.Mocker()
    def test_submit_invalid(self, rmock):
        self.mock_get_api_token_request(rmock)
        rmock.post(
            "https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/applications",
            status_code=400,
            json={
                "errors": [
                    {
                        "api_specification_url": "https://devstore.wellsfargo.com/store",
                        "description": "'ssn' is invalid.",
                        "error_code": "400-008",
                        "field_name": "main_applicant.ssn",
                    }
                ]
            },
        )

        self.client.login(username="joe", password="schmoe")

        url = reverse(self.view_name)
        data = self.build_valid_request()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("non_field_errors" in response.data)
        self.assertEqual(len(response.data["non_field_errors"]), 1)
        self.assertEqual(str(response.data["non_field_errors"][0]), "'ssn' is invalid.")

    @requests_mock.Mocker()
    def test_submit_denied(self, rmock):
        self.mock_get_api_token_request(rmock)
        self.mock_denied_credit_app_request(rmock)

        self.client.login(username="joe", password="schmoe")

        url = reverse(self.view_name)
        data = self.build_valid_request()
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Credit Application was denied by Wells Fargo"
        )

    @requests_mock.Mocker()
    def test_submit_pending(self, rmock):
        self.mock_get_api_token_request(rmock)
        self.mock_pending_credit_app_request(rmock)

        self.client.login(username="joe", password="schmoe")

        url = reverse(self.view_name)
        data = self.build_valid_request()
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Credit Application approval is pending"
        )
