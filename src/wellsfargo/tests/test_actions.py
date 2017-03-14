from decimal import Decimal
from django.core.exceptions import ValidationError
from ..connector import actions
from ..core.constants import CREDIT_APP_APPROVED
from ..core.exceptions import CreditApplicationDenied, TransactionDenied
from ..core.structures import TransactionRequest
from ..models import FinancingPlan
from .base import BaseTest
from . import responses
import mock


class SubmitTransactionTest(BaseTest):
    @mock.patch('soap.get_transport')
    def test_submit_transaction_success(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.transaction_successful)

        plan = FinancingPlan.objects.create(plan_number='1001', description='', apr=0, term_months=0)

        # Authorize a change against the credit line
        request = TransactionRequest()
        request.user = self.joe
        request.account_number = '9999999999999991'
        request.plan_number = plan.plan_number
        request.amount = Decimal('2159.99')
        request.ticket_number = 'D1234567890'
        transfer = actions.submit_transaction(request)

        # Should return a valid transfer object
        self.assertEqual(transfer.user, self.joe)
        self.assertEqual(transfer.merchant_reference, '6f9c34ae-2153-11e6-a8c1-0242ac110003')
        self.assertEqual(transfer.amount, Decimal('2159.99'))
        self.assertEqual(transfer.type_code, '5')
        self.assertEqual(transfer.ticket_number, 'D1234567890')
        self.assertEqual(transfer.financing_plan.plan_number, 1001)
        self.assertEqual(transfer.auth_number, '000000')
        self.assertEqual(transfer.status, 'A1')
        self.assertTrue(transfer.message.startswith('APPROVED'))
        self.assertTrue(transfer.disclosure.startswith('(DEMO) REGULAR TERMS'))


    @mock.patch('soap.get_transport')
    def test_submit_transaction_denied(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.transaction_denied)

        plan = FinancingPlan.objects.create(plan_number='1001', description='', apr=0, term_months=0)

        # Authorize a change against the credit line
        request = TransactionRequest()
        request.user = self.joe
        request.account_number = '9999999999999990'
        request.plan_number = plan.plan_number
        request.amount = Decimal('2159.99')
        request.ticket_number = 'D1234567890'

        with self.assertRaises(TransactionDenied):
            actions.submit_transaction(request)


class CreditInquiryTest(BaseTest):
    @mock.patch('soap.get_transport')
    def test_submit_inquiry_success(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.inquiry_successful)
        # Inquire as to the status of the account
        resp = actions.submit_inquiry('9999999999999991')
        self.assertEqual(resp.transaction_status, 'I0')
        self.assertEqual(resp.account_number, '9999999999999991')
        self.assertEqual(resp.balance, Decimal('0.00'))
        self.assertEqual(resp.open_to_buy, Decimal('5000.00'))
        self.assertEqual(resp.credit_limit, Decimal('5000.00'))


    @mock.patch('soap.get_transport')
    def test_submit_inquiry_failure(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.inquiry_failed)
        # Account is invalid
        with self.assertRaises(ValidationError):
            actions.submit_inquiry('9999999999999990')



class CreditApplicationTest(BaseTest):
    @mock.patch('soap.get_transport')
    def test_us_submit_single(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_successful)

        app = self._build_us_single_credit_app('999999990')
        self.assertFalse(app.is_joint)

        resp = actions.submit_credit_application(app)
        self.assertEqual(resp.application, app)
        self.assertEqual(resp.transaction_status, CREDIT_APP_APPROVED)
        self.assertEqual(resp.account_number, '9999999999999999')
        self.assertEqual(resp.credit_limit, Decimal('7500.00'))
        self.assertEqual(resp.balance, Decimal('0.00'))
        self.assertEqual(resp.open_to_buy, Decimal('7500.00'))


    @mock.patch('soap.get_transport')
    def test_us_submit_joint(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_successful)

        app = self._build_us_joint_credit_app('999999990', '999999990')
        self.assertTrue(app.is_joint)

        resp = actions.submit_credit_application(app)
        self.assertEqual(resp.application, app)
        self.assertEqual(resp.transaction_status, CREDIT_APP_APPROVED)
        self.assertEqual(resp.account_number, '9999999999999999')
        self.assertEqual(resp.credit_limit, Decimal('7500.00'))
        self.assertEqual(resp.balance, Decimal('0.00'))
        self.assertEqual(resp.open_to_buy, Decimal('7500.00'))


    @mock.patch('soap.get_transport')
    def test_missing_ssn(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_missing_ssn)
        app = self._build_us_single_credit_app(None)
        with self.assertRaises(ValidationError):
            actions.submit_credit_application(app)


    @mock.patch('soap.get_transport')
    def test_invalid_ssn(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_invalid_ssn)
        app = self._build_us_single_credit_app(None)
        with self.assertRaises(ValidationError):
            actions.submit_credit_application(app)


    @mock.patch('soap.get_transport')
    def test_submit_denied(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_denied)
        app = self._build_us_single_credit_app('999999994')
        with self.assertRaises(CreditApplicationDenied):
            actions.submit_credit_application(app)
