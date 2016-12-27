from decimal import Decimal
from django.contrib.auth.models import User, Group
from oscar.core.loading import get_model
from oscar_accounts import core, facade
from .base import BaseTest
from ..core.structures import AccountInquiryResult, CreditApplicationResult
from ..models import APICredentials

Account = get_model('oscar_accounts', 'Account')


class APICredentialsTest(BaseTest):
    def test_selection_no_user(self):
        APICredentials.objects.create(
            username='credsA',
            password='',
            merchant_num='',
            user_group=None,
            priority=1)
        APICredentials.objects.create(
            username='credsB',
            password='',
            merchant_num='',
            user_group=None,
            priority=2)
        self.assertEqual(APICredentials.get_credentials().username, 'credsB')


    def test_selection_user_no_group(self):
        APICredentials.objects.create(
            username='credsA',
            password='',
            merchant_num='',
            user_group=None,
            priority=1)
        APICredentials.objects.create(
            username='credsB',
            password='',
            merchant_num='',
            user_group=None,
            priority=2)
        user = User.objects.create_user(username='bill')
        self.assertEqual(APICredentials.get_credentials(user).username, 'credsB')

    def test_selection_user_group(self):
        group = Group.objects.create(name='Special Group')
        APICredentials.objects.create(
            username='credsA',
            password='',
            merchant_num='',
            user_group=None,
            priority=1)
        APICredentials.objects.create(
            username='credsB',
            password='',
            merchant_num='',
            user_group=group,
            priority=2)
        user = User.objects.create_user(username='bill')
        self.assertEqual(APICredentials.get_credentials(user).username, 'credsA')
        user.groups.add(group)
        self.assertEqual(APICredentials.get_credentials(user).username, 'credsB')
        user.groups.remove(group)
        self.assertEqual(APICredentials.get_credentials(user).username, 'credsA')


class AccountInquiryResultTest(BaseTest):
    def test_reconcilation(self):
        source = self._build_account('9999999999999991')
        dest = core.redemptions_account()

        # Test initial state of the account
        self.assertEqual(source.credit_limit, Decimal('7500.00'))
        self.assertEqual(source.balance, Decimal('0.00'))

        # Buy something
        facade.transfer(
            source=source,
            destination=dest,
            amount=Decimal('999.99'))

        # Check account balance
        self.assertEqual(source.credit_limit, Decimal('7500.00'))
        self.assertEqual(source.balance, Decimal('-999.99'))

        # Build a fake inquiry response that shows they haven't paid anything yet
        inquiry = AccountInquiryResult()
        inquiry.account = source
        inquiry.balance = Decimal('999.99')
        inquiry.open_to_buy = Decimal('6500.01')
        inquiry.reconcile()

        # Check account balance
        self.assertEqual(source.credit_limit, Decimal('7500.00'))
        self.assertEqual(source.balance, Decimal('-999.99'))

        # Customer made a payment
        inquiry = AccountInquiryResult()
        inquiry.account = source
        inquiry.balance = Decimal('800.00')
        inquiry.open_to_buy = Decimal('6700.00')
        inquiry.reconcile()

        # Check account balance
        self.assertEqual(source.credit_limit, Decimal('7500.00'))
        self.assertEqual(source.balance, Decimal('-800.00'))

        # Wells Fargo lowered the Customer's credit limit
        inquiry = AccountInquiryResult()
        inquiry.account = source
        inquiry.balance = Decimal('800.00')
        inquiry.open_to_buy = Decimal('6000.00')
        inquiry.reconcile()

        # Check account balance
        self.assertEqual(source.credit_limit, Decimal('6800.00'))
        self.assertEqual(source.balance, Decimal('-800.00'))

        # Wells Fargo lowered the Customer's credit limit again and the customer made a payment
        inquiry = AccountInquiryResult()
        inquiry.account = source
        inquiry.balance = Decimal('700.00')
        inquiry.open_to_buy = Decimal('5000.00')
        inquiry.reconcile()

        # Check account balance
        self.assertEqual(source.credit_limit, Decimal('5700.00'))
        self.assertEqual(source.balance, Decimal('-700.00'))


class CreditApplicationResultTest(BaseTest):
    def test_is_approved(self):
        result = self._build_app_result('999999990', 'E0')
        self.assertTrue(result.is_approved)

        result = self._build_app_result('999999990', 'E1')
        self.assertFalse(result.is_approved)

        result = self._build_app_result('999999990', 'E2')
        self.assertFalse(result.is_approved)

        result = self._build_app_result('999999990', 'E3')
        self.assertFalse(result.is_approved)

        result = self._build_app_result('999999990', 'E4')
        self.assertFalse(result.is_approved)


    def test_declined_save(self):
        result = self._build_app_result('999999990', 'E1')
        acct = result.save()
        self.assertIsNone(acct)


    def test_approved_save_user(self):
        result = self._build_app_result('999999990', 'E0')
        account = result.save()
        self.assertEqual(account.account_type.name, 'Credit Line (Wells Fargo)')
        self.assertEqual(account.code, '9999999999999991')
        self.assertEqual(account.name, 'Joe Schmoe – xxxxxxxxxxxx9991')
        self.assertEqual(account.primary_user.username, 'joe')
        self.assertEqual(account.status, 'Open')
        self.assertEqual(account.credit_limit, Decimal('7500.00'))
        self.assertEqual(account.wfrs_metadata.locale, 'en_US')
        self.assertEqual(account.wfrs_metadata.account_number, '9999999999999991')


    def _build_app_result(self, ssn, status):
        app = self._build_us_single_credit_app(ssn)
        result = CreditApplicationResult()
        result.application = app
        result.transaction_status = status
        result.account_number = '9999999999999991'
        result.credit_limit = Decimal('7500.00')
        return result
