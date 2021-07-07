from decimal import Decimal
from django.core.exceptions import ValidationError
from unittest import mock
from wellsfargo.core.exceptions import CreditApplicationDenied, CreditApplicationPending
from wellsfargo.connector.applications import CreditApplicationsAPIClient
from wellsfargo.tests.base import BaseTest
import requests_mock
import json


class CreditApplicationsAPIClientTest(BaseTest):
    @requests_mock.Mocker()
    @mock.patch("wellsfargo.core.signals.wfrs_app_approved.send")
    def test_single_application_success(self, rmock, wfrs_app_approved):
        self.mock_get_api_token_request(rmock)

        def match_credit_app_request(request):
            # Check auth header
            self.assertTrue(request.headers["Authorization"].startswith("Bearer "))
            # Check data in body
            data = json.loads(request.body)
            self.assertEqual(
                data,
                {
                    "language_preference": "E",
                    "main_applicant": {
                        "address": {
                            "address_line_1": "123 Evergreen Terrace",
                            "city": "Springfield",
                            "postal_code": "10001",
                            "state_code": "NY",
                        },
                        "annual_income": 150000,
                        "date_of_birth": "1991-01-01",
                        "email_address": "foo@example.com",
                        "employer_name": "self",
                        "first_name": "Joe",
                        "home_phone": "2122091333",
                        "housing_status": "Rent",
                        "last_name": "Schmoe",
                        "mobile_phone": "2122091333",
                        "ssn": "999999990",
                        "work_phone": "2122091333",
                    },
                    "merchant_number": "1111111111111111",
                    "requested_credit_limit": 2000,
                    "transaction_code": "A6",
                },
            )
            return True

        self.mock_successful_credit_app_request(
            rmock, additional_matcher=match_credit_app_request
        )

        app = self._build_single_credit_app("999999990")

        acct_details = CreditApplicationsAPIClient().submit_credit_application(app)

        wfrs_app_approved.assert_called_once_with(sender=app.__class__, app=app)

        self.assertEqual(acct_details.account_number, "9999999999999999")
        self.assertEqual(acct_details.main_applicant_full_name, "Schmoe, Joe")
        self.assertEqual(acct_details.joint_applicant_full_name, None)
        self.assertEqual(
            acct_details.main_applicant_address.address_line_1, "123 Evergreen Terrace"
        )
        self.assertEqual(acct_details.main_applicant_address.city, "Springfield")
        self.assertEqual(acct_details.main_applicant_address.postal_code, "10001")
        self.assertEqual(acct_details.main_applicant_address.state_code, "NY")
        self.assertEqual(acct_details.joint_applicant_address, None)
        self.assertEqual(acct_details.credit_limit, Decimal("7500.00"))
        self.assertEqual(acct_details.available_credit, Decimal("7500.00"))

    @requests_mock.Mocker()
    @mock.patch("wellsfargo.core.signals.wfrs_app_approved.send")
    def test_joint_application_success(self, rmock, wfrs_app_approved):
        self.mock_get_api_token_request(rmock)

        def match_credit_app_request(request):
            # Check auth header
            self.assertTrue(request.headers["Authorization"].startswith("Bearer "))
            # Check data in body
            data = json.loads(request.body)
            self.assertEqual(
                data,
                {
                    "language_preference": "E",
                    "main_applicant": {
                        "address": {
                            "address_line_1": "123 Evergreen Terrace",
                            "city": "Springfield",
                            "postal_code": "10001",
                            "state_code": "NY",
                        },
                        "annual_income": 150000,
                        "date_of_birth": "1991-01-01",
                        "email_address": "foo@example.com",
                        "employer_name": "self",
                        "first_name": "Joe",
                        "home_phone": "2122091333",
                        "housing_status": "Rent",
                        "last_name": "Schmoe",
                        "mobile_phone": "2122091333",
                        "ssn": "999999990",
                        "work_phone": "2122091333",
                    },
                    "joint_applicant": {
                        "address": {
                            "address_line_1": "123 Evergreen Terrace",
                            "city": "Springfield",
                            "postal_code": "10001",
                            "state_code": "NY",
                        },
                        "annual_income": 150000,
                        "date_of_birth": "1991-01-01",
                        "email_address": "foo@example.com",
                        "employer_name": "self",
                        "first_name": "Joe",
                        "home_phone": "2122091333",
                        # "housing_status": "Rent",
                        "last_name": "Schmoe",
                        "mobile_phone": "2122091333",
                        "ssn": "999999990",
                        "work_phone": "2122091333",
                    },
                    "merchant_number": "1111111111111111",
                    "requested_credit_limit": 2000,
                    "transaction_code": "A6",
                },
            )
            return True

        self.mock_successful_credit_app_request(
            rmock, additional_matcher=match_credit_app_request
        )

        app = self._build_joint_credit_app("999999990", "999999990")

        acct_details = CreditApplicationsAPIClient().submit_credit_application(app)

        wfrs_app_approved.assert_called_once_with(sender=app.__class__, app=app)

        self.assertEqual(acct_details.account_number, "9999999999999999")
        self.assertEqual(acct_details.main_applicant_full_name, "Schmoe, Joe")
        self.assertEqual(acct_details.joint_applicant_full_name, "Schmoe, Joe")
        self.assertEqual(
            acct_details.main_applicant_address.address_line_1, "123 Evergreen Terrace"
        )
        self.assertEqual(acct_details.main_applicant_address.city, "Springfield")
        self.assertEqual(acct_details.main_applicant_address.postal_code, "10001")
        self.assertEqual(acct_details.main_applicant_address.state_code, "NY")
        self.assertEqual(
            acct_details.joint_applicant_address.address_line_1, "123 Evergreen Terrace"
        )
        self.assertEqual(acct_details.joint_applicant_address.city, "Springfield")
        self.assertEqual(acct_details.joint_applicant_address.postal_code, "10001")
        self.assertEqual(acct_details.joint_applicant_address.state_code, "NY")
        self.assertEqual(acct_details.credit_limit, Decimal("7500.00"))
        self.assertEqual(acct_details.available_credit, Decimal("7500.00"))

    @requests_mock.Mocker()
    @mock.patch("wellsfargo.core.signals.wfrs_app_approved.send")
    def test_submit_denied(self, rmock, wfrs_app_approved):
        self.mock_get_api_token_request(rmock)
        self.mock_denied_credit_app_request(rmock)
        app = self._build_single_credit_app("999999994")
        with self.assertRaises(CreditApplicationDenied):
            CreditApplicationsAPIClient().submit_credit_application(app)
        wfrs_app_approved.assert_not_called()

    @requests_mock.Mocker()
    @mock.patch("wellsfargo.core.signals.wfrs_app_approved.send")
    def test_submit_pending(self, rmock, wfrs_app_approved):
        self.mock_get_api_token_request(rmock)
        self.mock_pending_credit_app_request(rmock)
        app = self._build_single_credit_app("999999991")
        with self.assertRaises(CreditApplicationPending):
            CreditApplicationsAPIClient().submit_credit_application(app)
        wfrs_app_approved.assert_not_called()

    @requests_mock.Mocker()
    @mock.patch("wellsfargo.core.signals.wfrs_app_approved.send")
    def test_validation_error(self, rmock, wfrs_app_approved):
        self.mock_get_api_token_request(rmock)
        rmock.post(
            "https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/applications",
            status_code=400,
            json={
                "errors": [
                    {
                        "api_specification_url": "https://devstore.wellsfargo.com/store",
                        "description": "'last_name' is missing from the body of the request.",
                        "error_code": "400-008",
                        "field_name": "main_applicant.last_name",
                    }
                ]
            },
        )
        app = self._build_single_credit_app("999999990")
        with self.assertRaises(ValidationError):
            CreditApplicationsAPIClient().submit_credit_application(app)
        wfrs_app_approved.assert_not_called()
