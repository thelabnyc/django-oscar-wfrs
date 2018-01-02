from datetime import date
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from soap.tests import SoapTest
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
