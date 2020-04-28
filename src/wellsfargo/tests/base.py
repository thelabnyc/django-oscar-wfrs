from datetime import date
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APITestCase
from wellsfargo.core.constants import (
    TRANS_DECLINED,
    TRANS_APPROVED,
)
from wellsfargo.models import (
    CreditApplicationAddress,
    CreditApplicationApplicant,
    CreditApplication,
    APIMerchantNum,
    SDKMerchantNum,
)


class BaseTest(APITestCase):
    fixtures = ['wfrs-test']

    def setUp(self):
        cache.clear()
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
        self.credentials = APIMerchantNum.objects.create(
            merchant_num='1111111111111111',
            user_group=None,
            priority=1)
        self.sdk_credentials = SDKMerchantNum.objects.create(
            merchant_num='1111111111112222',
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


    def mock_successful_credit_app_request(self, rmock, **kwargs):
        rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/applications',
            json={
                "client-request-id": "13391af9-0d04-4162-b84d-ab8080ec93fc",
                "transaction_code": "A6",
                "application_status": "APPROVED",
                "merchant_number": "1111111111111111",
                "credit_card_number": "9999999999999999",
                "credit_card_last_four": "9999",
                "credit_line": "7500.0"
            },
            **kwargs)


    def mock_denied_credit_app_request(self, rmock, **kwargs):
        rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/applications',
            json={
                "client-request-id": "13391af9-0d04-4162-b84d-ab8080ec93fc",
                "application_status": "DENIED",
            },
            **kwargs)


    def mock_pending_credit_app_request(self, rmock, **kwargs):
        rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/applications',
            json={
                "client-request-id": "13391af9-0d04-4162-b84d-ab8080ec93fc",
                "transaction_code": "A6",
                "application_status": "PENDING",
                "merchant_number": "1111111111111111",
                "credit_card_number": "9999999999999999",
                "credit_card_last_four": "9999",
                "credit_line": "7500.0"
            },
            **kwargs)


    def mock_successful_individual_account_inquiry(self, rmock, **kwargs):
        rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/details',
            json={
                "merchant_number": "1111111111111111",
                "transaction_code": "C1",
                "unique_id": "00001DGh",
                "account_number": "2222222222222222",
                "transaction_status": "H1",
                "available_credit": "14455.00",
                "credit_limit": "18000.00",
                "individual_joint_indicator": "I",
                "applicant": {
                    "name": "Schmoe, Joe",
                    "address": {
                        "address_1": "123 FIRST STREET",
                        "address_2": "APT  456",
                        "city": "DES MOINES",
                        "state": "IA",
                        "postal_code": "50322"
                    }
                }
            },
            **kwargs)


    def mock_successful_joint_account_inquiry(self, rmock, **kwargs):
        rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/details',
            json={
                "merchant_number": "1111111111111111",
                "transaction_code": "C4",
                "unique_id": "00001DGh",
                "account_number": "2222222222222222",
                "transaction_status": "H1",
                "available_credit": "14455.00",
                "credit_limit": "18000.00",
                "individual_joint_indicator": "J",
                "applicant": {
                    "name": "Schmoe, Joe",
                    "address": {
                        "address_1": "123 FIRST STREET",
                        "address_2": "APT  456",
                        "city": "DES MOINES",
                        "state": "IA",
                        "postal_code": "50322"
                    }
                },
                "joint_applicant": {
                    "name": "Schmoe, Karen",
                    "address": {
                        "address_1": "19 ARLEN RD APT J",
                        "city": "BALTIMORE",
                        "state": "MD",
                        "postal_code": "21236-5152"
                    }
                }
            },
            **kwargs)


    def mock_failed_individual_account_inquiry(self, rmock, **kwargs):
        rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/details',
            status_code=400,
            json={
                'errors': [
                    {
                        'error_code': '400-015',
                        'description': "'account_number' cannot have fewer than 15 character(s).",
                        'field_name': 'account_number',
                        'field_value': '9999',
                        'api_specification_url': 'https://devstore.wellsfargo.com/store',
                    },
                ],
            },
            **kwargs)


    def mock_pending_individual_account_inquiry(self, rmock, **kwargs):
        rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/details',
            json={
                "merchant_number": "1111111111111111",
                "message": "Pending",
                "transaction_code": "C4",
                "transaction_status": "H7",
            },
            **kwargs)


    def mock_successful_prescreen_request(self, rmock, **kwargs):
        rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/prequalifications',
            json={
                "client-request-id": "f98ee81c-5bf3-4366-9388-f3759a54b4be",
                "merchant_number": "1111111111111111",
                "transaction_code": "MAH",
                "decision_status": "A",
                "application_id": "000005EP",
                "max_credit_limit": "8500",
                "decision_message": "APPROVED",
                "URL": "",
            },
            **kwargs)


    def mock_denied_prescreen_request(self, rmock, **kwargs):
        rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/prequalifications',
            json={
                "client-request-id": "f98ee81c-5bf3-4366-9388-f3759a54b4be",
                "transaction_code": "MAH",
                "decision_status": "D",
                "decision_message": "DENIED"
            },
            **kwargs)


    def mock_invalid_prescreen_request(self, rmock, **kwargs):
        rmock.post('https://api-sandbox.wellsfargo.com/credit-cards/private-label/new-accounts/v2/prequalifications',
            status_code=400,
            json={
                "errors": [
                    {
                        "error_code": "1027-013",
                        "description": "Return URL is missing or invalid.",
                        "api_specification_url": "https://devstore.wellsfargo.com/store"
                    }
                ]
            },
            **kwargs)


    def _build_single_credit_app(self, main_ssn):
        main_applicant_address = CreditApplicationAddress.objects.create(
            address_line_1='123 Evergreen Terrace',
            address_line_2='',
            city='Springfield',
            state_code='NY',
            postal_code='10001',
        )
        main_applicant = CreditApplicationApplicant.objects.create(
            first_name='Joe',
            last_name='Schmoe',
            middle_initial='',
            date_of_birth=date(1991, 1, 1),
            ssn=main_ssn,
            annual_income=150_000,
            email_address='foo@example.com',
            home_phone='+1 (212) 209-1333',
            mobile_phone='+1 (212) 209-1333',
            work_phone='+1 (212) 209-1333',
            employer_name='self',
            housing_status='Rent',
            address=main_applicant_address,
        )
        app = CreditApplication(
            requested_credit_limit=2_000,
            main_applicant=main_applicant,
        )
        return app


    def _build_joint_credit_app(self, main_ssn, joint_ssn):
        app = self._build_single_credit_app(main_ssn)
        joint_applicant_address = CreditApplicationAddress.objects.create(
            address_line_1='123 Evergreen Terrace',
            address_line_2='',
            city='Springfield',
            state_code='NY',
            postal_code='10001',
        )
        app.joint_applicant = CreditApplicationApplicant.objects.create(
            first_name='Joe',
            last_name='Schmoe',
            middle_initial='',
            date_of_birth=date(1991, 1, 1),
            ssn=joint_ssn,
            annual_income=150_000,
            email_address='foo@example.com',
            home_phone='+1 (212) 209-1333',
            mobile_phone='+1 (212) 209-1333',
            work_phone='+1 (212) 209-1333',
            employer_name='self',
            housing_status='Rent',
            address=joint_applicant_address,
        )
        return app
