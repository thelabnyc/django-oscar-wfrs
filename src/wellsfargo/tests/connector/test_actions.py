from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from wellsfargo.connector import actions
from wellsfargo.core.constants import (
    PREQUAL_TRANS_STATUS_APPROVED,
    PREQUAL_CUSTOMER_RESP_ACCEPT,
)
from wellsfargo.models import (
    PreQualificationRequest,
    PreQualificationResponse,
)
from wellsfargo.tests.base import BaseTest
from wellsfargo.tests import responses
from unittest import mock



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
        self.assertEqual(resp.available_credit, Decimal('5000.00'))
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
        request.save()

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
        request.save()

        with self.assertRaises(ValidationError):
            actions.check_pre_qualification_status(request)



class CheckPreQualificationAccountStatusTest(BaseTest):
    @mock.patch('soap.get_transport')
    def test_prequal_acct_status_success(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.otb_successful)

        request = PreQualificationRequest()
        request.first_name = 'Joe'
        request.last_name = 'Schmoe'
        request.line1 = '123 Evergreen Terrace'
        request.city = 'Springfield'
        request.state = 'NY'
        request.postcode = '10001'
        request.phone = '+1 (212) 209-1333'
        request.merchant_name = self.credentials.name
        request.merchant_num = self.credentials.merchant_num
        request.credentials = self.credentials
        request.save()

        prequal_resp = PreQualificationResponse()
        prequal_resp.request = request
        prequal_resp.status = PREQUAL_TRANS_STATUS_APPROVED
        prequal_resp.message = "pass"
        prequal_resp.offer_indicator = 'F1'
        prequal_resp.credit_limit = Decimal('5000.00')
        prequal_resp.response_id = '00000TKA'
        prequal_resp.application_url = 'https://localhost/ipscr.do?id=u64RVNDAAAAICbmCjLaoQIJNSOJhojOkEssokkO3WvGBqdOxl_4BfA.'
        prequal_resp.customer_response = PREQUAL_CUSTOMER_RESP_ACCEPT
        prequal_resp.customer_order = None
        prequal_resp.reported_datetime = timezone.now()
        prequal_resp.save()

        account_resp = actions.check_pre_qualification_account_status(prequal_resp)

        self.assertEqual(account_resp.prequal_response_source, prequal_resp)
        self.assertEqual(account_resp.status, 'H0')
        self.assertEqual(account_resp.last4_account_number, '9999')
        self.assertEqual(account_resp.account_number, '9999999999999999')
        self.assertEqual(account_resp.first_name, 'Joe')
        self.assertEqual(account_resp.middle_initial, '')
        self.assertEqual(account_resp.last_name, 'Schmoe')
        self.assertEqual(account_resp.phone_number, '+12122091333')
        self.assertEqual(account_resp.address, '123 Evergreen Terrace')
        self.assertEqual(account_resp.credit_limit, Decimal('9000.00'))
        self.assertEqual(account_resp.balance, Decimal('500.00'))
        self.assertEqual(account_resp.available_credit, Decimal('8500.00'))
        self.assertEqual(account_resp.last_payment_date, None)
        self.assertEqual(account_resp.last_payment_amount, None)
        self.assertEqual(account_resp.payment_due_date, None)
        self.assertEqual(account_resp.payment_due_amount, None)


    @mock.patch('soap.get_transport')
    def test_prequal_acct_status_denied(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.otb_denied)

        request = PreQualificationRequest()
        request.first_name = 'Joe'
        request.last_name = 'Schmoe'
        request.line1 = '123 Evergreen Terrace'
        request.city = 'Springfield'
        request.state = 'NY'
        request.postcode = '10001'
        request.phone = '+1 (212) 209-1333'
        request.merchant_name = self.credentials.name
        request.merchant_num = self.credentials.merchant_num
        request.credentials = self.credentials
        request.save()

        prequal_resp = PreQualificationResponse()
        prequal_resp.request = request
        prequal_resp.status = PREQUAL_TRANS_STATUS_APPROVED
        prequal_resp.message = "pass"
        prequal_resp.offer_indicator = 'F1'
        prequal_resp.credit_limit = Decimal('5000.00')
        prequal_resp.response_id = '00000TKA'
        prequal_resp.application_url = 'https://localhost/ipscr.do?id=u64RVNDAAAAICbmCjLaoQIJNSOJhojOkEssokkO3WvGBqdOxl_4BfA.'
        prequal_resp.customer_response = PREQUAL_CUSTOMER_RESP_ACCEPT
        prequal_resp.customer_order = None
        prequal_resp.reported_datetime = timezone.now()
        prequal_resp.save()

        account_resp = actions.check_pre_qualification_account_status(prequal_resp)
        self.assertEqual(account_resp, None)


    @mock.patch('soap.get_transport')
    def test_prequal_acct_status_error(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.otb_error)

        request = PreQualificationRequest()
        request.first_name = 'Joe'
        request.last_name = 'Schmoe'
        request.line1 = '123 Evergreen Terrace'
        request.city = 'Springfield'
        request.state = 'NY'
        request.postcode = '10001'
        request.phone = '+1 (212) 209-1333'
        request.merchant_name = self.credentials.name
        request.merchant_num = self.credentials.merchant_num
        request.credentials = self.credentials
        request.save()

        prequal_resp = PreQualificationResponse()
        prequal_resp.request = request
        prequal_resp.status = PREQUAL_TRANS_STATUS_APPROVED
        prequal_resp.message = "pass"
        prequal_resp.offer_indicator = 'F1'
        prequal_resp.credit_limit = Decimal('5000.00')
        prequal_resp.response_id = '00000TKA'
        prequal_resp.application_url = 'https://localhost/ipscr.do?id=u64RVNDAAAAICbmCjLaoQIJNSOJhojOkEssokkO3WvGBqdOxl_4BfA.'
        prequal_resp.customer_response = PREQUAL_CUSTOMER_RESP_ACCEPT
        prequal_resp.customer_order = None
        prequal_resp.reported_datetime = timezone.now()
        prequal_resp.save()

        with self.assertRaises(ValidationError):
            actions.check_pre_qualification_account_status(prequal_resp)
