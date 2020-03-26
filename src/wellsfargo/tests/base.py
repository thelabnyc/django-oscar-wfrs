from datetime import date
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from soap.tests import SoapTest
from wellsfargo.core.constants import (
    TRANS_DECLINED,
    TRANS_APPROVED,
)
from wellsfargo.models import USCreditApp, USJointCreditApp, APICredentials


class BaseTest(SoapTest, APITestCase):
    fixtures = ['wfrs-test']

    def setUp(self):
        self.joe = User.objects.create_user(
            username='joe',
            password='schmoe',
            email='joe@example.com')
        self.bill = User.objects.create_user(
            username='bill',
            password='schmoe',
            is_staff=True,
            is_superuser=True,
            email='bill@example.com')
        self.credentials = APICredentials.objects.create(
            username='WF1111111111111111',
            password='FOOBAR',
            merchant_num='1111111111111111',
            user_group=None,
            priority=1)
        return super().setUp()


    def mock_get_api_token_request(self, rmock):
        rmock.post('https://api-sandbox.wellsfargo.com/token', json={
            "access_token": "16a05f65dd41569af67dbdca7ea4da4d",
            "scope": "",
            "token_type": "Bearer",
            "expires_in": 79900,
        })


    def mock_successful_transaction_request(self, rmock, **kwargs):
        rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/payment/transactions/authorization',
            json={
                "client-request-id": "c17381a3-22fa-4463-8b0a-a3c18f6c4a44",
                "status_message": "APPROVED: 123434",
                "transaction_status": TRANS_APPROVED,
                "plan_number": "9999",
                "ticket_number": "123444",
                "disclosure": "REGULAR TERMS WITH REGULAR PAYMENTS. THE REGULAR RATE IS 28.99%.",
                "authorization_number": "000000",
                "transaction_type": "AUTHORIZATION",
                "account_number": "9999999999999991",
                "amount": "2159.99"
            },
            **kwargs)


    def mock_declined_transaction_request(self, rmock, **kwargs):
        rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/payment/transactions/authorization',
            json={
                "transaction_status": TRANS_DECLINED,
            },
            **kwargs)


    def _build_us_single_credit_app(self, main_ssn):
        app = USCreditApp()
        app.user = self.joe
        app.region = 'US'
        app.language = 'E'
        app.purchase_price = 2000
        app.app_type = 'I'
        app.main_first_name = 'Joe'
        app.main_last_name = 'Schmoe'
        app.main_date_of_birth = date(1991, 1, 1)
        app.main_address_line1 = '123 Evergreen Terrace'
        app.main_address_city = 'Springfield'
        app.main_home_value = '200000'
        app.main_mortgage_balance = '50000'
        app.main_annual_income = '150000'
        app.email = 'foo@example.com'
        app.main_ssn = main_ssn
        app.main_address_state = 'NY'
        app.main_address_postcode = '10001'
        app.main_home_phone = '+1 (212) 209-1333'
        app.main_employer_phone = '+1 (212) 209-1333'
        return app

    def _build_us_joint_credit_app(self, main_ssn, joint_ssn):
        app = USJointCreditApp()
        app.user = self.joe
        app.region = 'US'
        app.language = 'E'
        app.app_type = 'I'
        app.main_first_name = 'Joe'
        app.main_last_name = 'Schmoe'
        app.main_date_of_birth = date(1991, 1, 1)
        app.main_address_line1 = '123 Evergreen Terrace'
        app.main_address_city = 'Springfield'
        app.main_home_value = '200000'
        app.main_mortgage_balance = '50000'
        app.main_annual_income = '150000'
        app.email = 'foo@example.com'
        app.main_ssn = main_ssn
        app.main_address_state = 'NY'
        app.main_address_postcode = '10001'
        app.main_home_phone = '+1 (212) 209-1333'
        app.main_employer_phone = '+1 (212) 209-1333'
        app.joint_first_name = 'Jill'
        app.joint_last_name = 'Schmoe'
        app.joint_date_of_birth = date(1991, 1, 1)
        app.joint_address_line1 = '123 Evergreen Terrace'
        app.joint_address_city = 'Springfield'
        app.joint_annual_income = '30000'
        app.joint_ssn = joint_ssn
        app.joint_address_state = 'NY'
        app.joint_address_postcode = '10001'
        app.joint_employer_phone = '+1 (212) 209-1333'
        return app
