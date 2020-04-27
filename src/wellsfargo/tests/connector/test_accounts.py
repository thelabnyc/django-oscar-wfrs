from decimal import Decimal
from django.core.exceptions import ValidationError
from wellsfargo.connector.accounts import AccountsAPIClient
from wellsfargo.tests.base import BaseTest
import requests_mock
import json



class AccountsAPIClientTest(BaseTest):

    @requests_mock.Mocker()
    def test_lookup_account_by_prequal_offer_id_success(self, rmock):
        self.mock_get_api_token_request(rmock)

        def match_request(request):
            # Check auth header
            self.assertTrue(request.headers['Authorization'].startswith('Bearer '))
            # Check data in body
            data = json.loads(request.body)
            self.assertEqual(data, {
                'locale': 'en_US',
                'merchant_number': '1111111111111111',
                'transaction_code': 'C1',
                'first_name': 'Joe',
                'last_name': 'Schmoe',
                'unique_id': '00001DGh',
            })
            return True

        self.mock_successful_individual_account_inquiry(rmock, additional_matcher=match_request)

        inquiry = AccountsAPIClient().lookup_account_by_prequal_offer_id(
            first_name='Joe',
            last_name='Schmoe',
            unique_id='00001DGh')

        self.assertEqual(inquiry.credit_app_source, None)
        self.assertEqual(inquiry.prequal_response_source, None)
        self.assertEqual(inquiry.main_applicant_full_name, 'Schmoe, Joe')
        self.assertEqual(inquiry.joint_applicant_full_name, None)
        self.assertEqual(inquiry.main_applicant_address.address_line_1, '123 FIRST STREET')
        self.assertEqual(inquiry.main_applicant_address.address_line_2, 'APT  456')
        self.assertEqual(inquiry.main_applicant_address.city, 'DES MOINES')
        self.assertEqual(inquiry.main_applicant_address.state_code, 'IA')
        self.assertEqual(inquiry.main_applicant_address.postal_code, '50322')
        self.assertEqual(inquiry.joint_applicant_address, None)
        self.assertEqual(inquiry.credit_limit, Decimal('18000.00'))
        self.assertEqual(inquiry.available_credit, Decimal('14455.00'))


    @requests_mock.Mocker()
    def test_lookup_account_by_metadata_success(self, rmock):
        self.mock_get_api_token_request(rmock)

        def match_request(request):
            # Check auth header
            self.assertTrue(request.headers['Authorization'].startswith('Bearer '))
            # Check data in body
            data = json.loads(request.body)
            self.assertEqual(data, {
                'locale': 'en_US',
                'merchant_number': '1111111111111111',
                'transaction_code': 'C2',
                'first_name': 'Joe',
                'last_name': 'Schmoe',
                'postal_code': '10001',
            })
            return True

        self.mock_successful_individual_account_inquiry(rmock, additional_matcher=match_request)

        inquiry = AccountsAPIClient().lookup_account_by_metadata(
            first_name='Joe',
            last_name='Schmoe',
            postal_code='10001')

        self.assertEqual(inquiry.credit_app_source, None)
        self.assertEqual(inquiry.prequal_response_source, None)
        self.assertEqual(inquiry.main_applicant_full_name, 'Schmoe, Joe')
        self.assertEqual(inquiry.joint_applicant_full_name, None)
        self.assertEqual(inquiry.main_applicant_address.address_line_1, '123 FIRST STREET')
        self.assertEqual(inquiry.main_applicant_address.address_line_2, 'APT  456')
        self.assertEqual(inquiry.main_applicant_address.city, 'DES MOINES')
        self.assertEqual(inquiry.main_applicant_address.state_code, 'IA')
        self.assertEqual(inquiry.main_applicant_address.postal_code, '50322')
        self.assertEqual(inquiry.joint_applicant_address, None)
        self.assertEqual(inquiry.credit_limit, Decimal('18000.00'))
        self.assertEqual(inquiry.available_credit, Decimal('14455.00'))


    @requests_mock.Mocker()
    def test_lookup_account_by_account_number_success(self, rmock):
        self.mock_get_api_token_request(rmock)

        def match_request(request):
            # Check auth header
            self.assertTrue(request.headers['Authorization'].startswith('Bearer '))
            # Check data in body
            data = json.loads(request.body)
            self.assertEqual(data, {
                'locale': 'en_US',
                'merchant_number': '1111111111111111',
                'transaction_code': 'C4',
                'account_number': '9999999999999999',
            })
            return True

        self.mock_successful_individual_account_inquiry(rmock, additional_matcher=match_request)

        inquiry = AccountsAPIClient().lookup_account_by_account_number(
            account_number='9999999999999999')

        self.assertEqual(inquiry.credit_app_source, None)
        self.assertEqual(inquiry.prequal_response_source, None)
        self.assertEqual(inquiry.main_applicant_full_name, 'Schmoe, Joe')
        self.assertEqual(inquiry.joint_applicant_full_name, None)
        self.assertEqual(inquiry.main_applicant_address.address_line_1, '123 FIRST STREET')
        self.assertEqual(inquiry.main_applicant_address.address_line_2, 'APT  456')
        self.assertEqual(inquiry.main_applicant_address.city, 'DES MOINES')
        self.assertEqual(inquiry.main_applicant_address.state_code, 'IA')
        self.assertEqual(inquiry.main_applicant_address.postal_code, '50322')
        self.assertEqual(inquiry.joint_applicant_address, None)
        self.assertEqual(inquiry.credit_limit, Decimal('18000.00'))
        self.assertEqual(inquiry.available_credit, Decimal('14455.00'))


    @requests_mock.Mocker()
    def test_lookup_account_by_account_number_joint_success(self, rmock):
        self.mock_get_api_token_request(rmock)
        self.mock_successful_joint_account_inquiry(rmock)

        inquiry = AccountsAPIClient().lookup_account_by_account_number(
            account_number='9999999999999999')

        self.assertEqual(inquiry.credit_app_source, None)
        self.assertEqual(inquiry.prequal_response_source, None)
        self.assertEqual(inquiry.main_applicant_full_name, 'Schmoe, Joe')
        self.assertEqual(inquiry.joint_applicant_full_name, 'Schmoe, Karen')

        self.assertEqual(inquiry.main_applicant_address.address_line_1, '123 FIRST STREET')
        self.assertEqual(inquiry.main_applicant_address.address_line_2, 'APT  456')
        self.assertEqual(inquiry.main_applicant_address.city, 'DES MOINES')
        self.assertEqual(inquiry.main_applicant_address.state_code, 'IA')
        self.assertEqual(inquiry.main_applicant_address.postal_code, '50322')

        self.assertEqual(inquiry.joint_applicant_address.address_line_1, '19 ARLEN RD APT J')
        self.assertEqual(inquiry.joint_applicant_address.address_line_2, '')
        self.assertEqual(inquiry.joint_applicant_address.city, 'BALTIMORE')
        self.assertEqual(inquiry.joint_applicant_address.state_code, 'MD')
        self.assertEqual(inquiry.joint_applicant_address.postal_code, '21236-5152')

        self.assertEqual(inquiry.credit_limit, Decimal('18000.00'))
        self.assertEqual(inquiry.available_credit, Decimal('14455.00'))


    @requests_mock.Mocker()
    def test_lookup_account_by_account_number_validation_error(self, rmock):
        self.mock_get_api_token_request(rmock)
        self.mock_failed_individual_account_inquiry(rmock)

        with self.assertRaises(ValidationError):
            AccountsAPIClient().lookup_account_by_account_number(
                account_number='9999')


    @requests_mock.Mocker()
    def test_lookup_account_by_account_number_account_still_pending(self, rmock):
        self.mock_get_api_token_request(rmock)
        self.mock_pending_individual_account_inquiry(rmock)

        inquiry = AccountsAPIClient().lookup_account_by_account_number(
            account_number='9999')
        self.assertIsNone(inquiry)
