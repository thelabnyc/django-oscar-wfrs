from decimal import Decimal
from django.core.exceptions import ValidationError
from oscar.core.loading import get_model
from oscar_accounts.core import redemptions_account
import mock

from .base import BaseTest
from . import responses

from ..connector import actions
from ..core.constants import CREDIT_APP_APPROVED
from ..core.exceptions import CreditApplicationDenied, TransactionDenied
from ..core.structures import TransactionRequest

Account = get_model('oscar_accounts', 'Account')



class SubmitTransactionTest(BaseTest):
    @mock.patch('soap.get_transport')
    def test_submit_transaction_success(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.transaction_successful)

        source = self._build_account('9999999999999991')

        # Authorize a change against the credit line
        request = TransactionRequest.build_auth_request(
            source_account=source,
            plan_number='1001',
            amount=Decimal('2159.99'),
            ticket_number='D1234567890')
        transfer = actions.submit_transaction(request)

        # Should return a valid transfer object
        self.assertEqual(transfer.amount, Decimal('2159.99'))
        self.assertEqual(transfer.wfrs_metadata.type_code, '5')
        self.assertEqual(transfer.wfrs_metadata.ticket_number, 'D1234567890')
        self.assertEqual(transfer.wfrs_metadata.plan_number, '1001')
        self.assertEqual(transfer.wfrs_metadata.auth_number, '000000')
        self.assertEqual(transfer.wfrs_metadata.status, 'A1')
        self.assertIsNotNone(transfer.wfrs_metadata.message)
        self.assertIsNotNone(transfer.wfrs_metadata.disclosure)

        # Check balances on source and destination account
        self.assertEqual(source.balance, Decimal('-2159.99'))
        self.assertEqual(redemptions_account().balance, Decimal('2159.99'))


    @mock.patch('soap.get_transport')
    def test_submit_transaction_denied(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.transaction_denied)

        source = self._build_account('9999999999999990')
        # Authorize a change against the credit line
        request = TransactionRequest.build_auth_request(
            source_account=source,
            plan_number='1001',
            amount=Decimal('2159.99'),
            ticket_number='D1234567890')

        def submit():
            actions.submit_transaction(request)
        self.assertRaises(TransactionDenied, submit)



class CreditInquiryTest(BaseTest):
    @mock.patch('soap.get_transport')
    def test_submit_inquiry_success(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.inquiry_successful)

        source = self._build_account('9999999999999991')
        # Inquire as to the status of the account
        resp = actions.submit_inquiry(source)
        self.assertEqual(resp.balance, Decimal('0.00'))
        self.assertEqual(resp.open_to_buy, Decimal('5000.00'))


    @mock.patch('soap.get_transport')
    def test_submit_inquiry_failure(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.inquiry_failed)

        source = self._build_account('9999999999999990')

        # Account is invalid
        def submit():
            actions.submit_inquiry(source)
        self.assertRaises(ValidationError, submit)



class CreditApplicationTest(BaseTest):
    @mock.patch('soap.get_transport')
    def test_us_submit_single(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_successful)

        app = self._build_us_single_credit_app('999999990')
        self.assertFalse(app.is_joint)

        resp = actions.submit_credit_application(app)
        self.assertEqual(resp.transaction_status, CREDIT_APP_APPROVED)
        self.assertEqual(resp.account_number, '9999999999999999')
        self.assertEqual(resp.credit_limit, Decimal('7500.00'))

        account = resp.save()
        self.assertEqual(account.account_type.name, 'Credit Line (Wells Fargo)')
        self.assertEqual(account.code, '9999999999999999')
        self.assertEqual(account.primary_user, None)
        self.assertEqual(account.status, 'Open')
        self.assertEqual(account.credit_limit, Decimal('7500.00'))


    @mock.patch('soap.get_transport')
    def test_us_submit_joint(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_successful)

        app = self._build_us_join_credit_app('999999990', '999999990')
        self.assertTrue(app.is_joint)

        resp = actions.submit_credit_application(app)
        self.assertEqual(resp.transaction_status, CREDIT_APP_APPROVED)
        self.assertEqual(resp.account_number, '9999999999999999')
        self.assertEqual(resp.credit_limit, Decimal('7500.00'))


    @mock.patch('soap.get_transport')
    def test_missing_ssn(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_invalid_ssn)

        app = self._build_us_single_credit_app(None)

        def submit():
            actions.submit_credit_application(app)
        self.assertRaises(ValidationError, submit)


    @mock.patch('soap.get_transport')
    def test_submit_denied(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_denied)

        app = self._build_us_single_credit_app('999999994')

        def submit():
            actions.submit_credit_application(app)
        self.assertRaises(CreditApplicationDenied, submit)
