from decimal import Decimal
from django.core.exceptions import ValidationError
from wellsfargo.connector import actions
from wellsfargo.core.exceptions import CreditApplicationPending, CreditApplicationDenied, TransactionDenied
from wellsfargo.core.structures import TransactionRequest
from wellsfargo.models import FinancingPlan, PreQualificationRequest
from wellsfargo.tests.base import BaseTest
from wellsfargo.tests import responses
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
        self.assertEqual(transfer.credentials, self.credentials)
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
        self.assertEqual(resp.account_number, '9999999999999991')
        self.assertEqual(resp.first_name, 'John')
        self.assertEqual(resp.middle_initial, 'Q')
        self.assertEqual(resp.last_name, 'Smith')
        self.assertEqual(resp.phone_number.as_e164, '+15559998888')
        self.assertEqual(resp.address, '123 First Street')
        self.assertEqual(resp.credit_limit, Decimal('5000.00'))
        self.assertEqual(resp.balance, Decimal('0.00'))
        self.assertEqual(resp.open_to_buy, Decimal('5000.00'))
        self.assertEqual(resp.last_payment_date, None)
        self.assertEqual(resp.last_payment_amount, Decimal('0.00'))
        self.assertEqual(resp.payment_due_date, None)
        self.assertEqual(resp.payment_due_amount, Decimal('0.00'))


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
        self.assertEqual(resp.account_number, '9999999999999999')
        self.assertEqual(resp.first_name, 'Joe')
        self.assertEqual(resp.middle_initial, None)
        self.assertEqual(resp.last_name, 'Schmoe')
        self.assertEqual(resp.phone_number.as_e164, '+12122091333')
        self.assertEqual(resp.address, '123 Evergreen Terrace')
        self.assertEqual(resp.credit_limit, Decimal('7500.00'))
        self.assertEqual(resp.balance, Decimal('0.00'))
        self.assertEqual(resp.open_to_buy, Decimal('7500.00'))
        self.assertEqual(resp.last_payment_date, None)
        self.assertEqual(resp.last_payment_amount, None)
        self.assertEqual(resp.payment_due_date, None)
        self.assertEqual(resp.payment_due_amount, None)


    @mock.patch('soap.get_transport')
    def test_us_submit_joint(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_successful)

        app = self._build_us_joint_credit_app('999999990', '999999990')
        self.assertTrue(app.is_joint)

        resp = actions.submit_credit_application(app)
        self.assertEqual(resp.account_number, '9999999999999999')
        self.assertEqual(resp.first_name, 'Joe')
        self.assertEqual(resp.middle_initial, None)
        self.assertEqual(resp.last_name, 'Schmoe')
        self.assertEqual(resp.phone_number.as_e164, '+12122091333')
        self.assertEqual(resp.address, '123 Evergreen Terrace')
        self.assertEqual(resp.credit_limit, Decimal('7500.00'))
        self.assertEqual(resp.balance, Decimal('0.00'))
        self.assertEqual(resp.open_to_buy, Decimal('7500.00'))
        self.assertEqual(resp.last_payment_date, None)
        self.assertEqual(resp.last_payment_amount, None)
        self.assertEqual(resp.payment_due_date, None)
        self.assertEqual(resp.payment_due_amount, None)


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


    @mock.patch('soap.get_transport')
    def test_submit_pending(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.credit_app_pending)
        app = self._build_us_single_credit_app('999999991')
        with self.assertRaises(CreditApplicationPending):
            actions.submit_credit_application(app)



class CheckPreQualificationStatusTest(BaseTest):
    @mock.patch('soap.get_transport')
    def test_prequal_success(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.prequal_successful)

        request = PreQualificationRequest()
        request.first_name = 'Joe'
        request.last_name = 'Schmoe'
        request.line1 = '123 Evergreen Terrace'
        request.city = 'Springfield'
        request.state = 'NY'
        request.postcode = '10001'
        request.phone = '+1 (212) 209-1333'

        resp = actions.check_pre_qualification_status(request)
        self.assertEqual(resp.request, request)
        self.assertEqual(resp.status, 'A')
        self.assertEqual(resp.is_approved, True)
        self.assertEqual(resp.message, 'approved')
        self.assertEqual(resp.offer_indicator, 'F1')
        self.assertEqual(resp.credit_limit, Decimal('8500.00'))
        self.assertEqual(resp.response_id, '000005EP')
        self.assertEqual(resp.application_url, 'https://localhost/ipscr.do?id=u64RVNDAAAAICbmCjLaoQIJNSOJhojOkEssokkO3WvGBqdOxl_4BfA.')
        self.assertEqual(resp.customer_response, '')


    @mock.patch('soap.get_transport')
    def test_prequal_failure(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.prequal_failed)

        request = PreQualificationRequest()
        request.first_name = 'Joe'
        request.last_name = 'Schmoe'
        request.line1 = '123 Evergreen Terrace'
        request.city = 'Springfield'
        request.state = 'NY'
        request.postcode = '10001'
        request.phone = '+1 (212) 209-1333'

        with self.assertRaises(ValidationError):
            actions.check_pre_qualification_status(request)
