from decimal import Decimal
from django.core.exceptions import ValidationError
from oscar.core.loading import get_model
from oscar_accounts.core import redemptions_account
import mock

from .base import BaseTest

from ..connector import actions
from ..core.constants import CREDIT_APP_APPROVED
from ..core.exceptions import CreditApplicationDenied, TransactionDenied
from ..core.structures import TransactionRequest

Account = get_model('oscar_accounts', 'Account')



class SubmitTransactionTest(BaseTest):
    @mock.patch('soap.get_transport')
    def test_submit_transaction_success(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(self._get_success_response())

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
        get_transport.return_value = self._build_transport_with_reply(self._get_denied_response())

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


    def _get_success_response(self):
        resp = b"""<?xml version="1.0" encoding="utf-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <soapenv:Body>
                    <ns1:submitTransactionResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="http://services.webservices.retaildealer.wff.com">
                        <submitTransactionReturn>
                            <accountNumber>9999999999999991</accountNumber>
                            <amount>2159.99</amount>
                            <authorizationNumber>000000</authorizationNumber>
                            <disclosure>(DEMO) REGULAR TERMS WITH REGULAR PAYMENTS. THE REGULAR RATE IS 27.99%. THIS APR WILL VARY WITH THE MARKET BASED ON THE PRIME RATE.</disclosure>
                            <faults xsi:nil="true"/>
                            <planNumber>1001</planNumber>
                            <ticketNumber>D1234567890</ticketNumber>
                            <transactionCode>5</transactionCode>
                            <transactionMessage>APPROVED: 000000</transactionMessage>
                            <transactionStatus>A1</transactionStatus>
                            <uuid>6f9c34ae-2153-11e6-a8c1-0242ac110003</uuid>
                        </submitTransactionReturn>
                    </ns1:submitTransactionResponse>
                </soapenv:Body>
            </soapenv:Envelope>"""
        return resp


    def _get_denied_response(self):
        resp = b"""<?xml version="1.0" encoding="utf-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <soapenv:Body>
                    <ns1:submitTransactionResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="http://services.webservices.retaildealer.wff.com">
                        <submitTransactionReturn>
                            <accountNumber>9999999999999990</accountNumber>
                            <amount>2159.99</amount>
                            <authorizationNumber>000000</authorizationNumber>
                            <disclosure/>
                            <faults xsi:nil="true"/>
                            <planNumber>1001</planNumber>
                            <ticketNumber>D1234567890</ticketNumber>
                            <transactionCode>5</transactionCode>
                            <transactionMessage>AUTH DENIED</transactionMessage>
                            <transactionStatus>A0</transactionStatus>
                            <uuid>6f87219a-2153-11e6-a8c1-0242ac110003</uuid>
                        </submitTransactionReturn>
                    </ns1:submitTransactionResponse>
                </soapenv:Body>
            </soapenv:Envelope>"""
        return resp




class CreditInquiryTest(BaseTest):
    @mock.patch('soap.get_transport')
    def test_submit_inquiry_success(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(self._get_success_response())

        source = self._build_account('9999999999999991')
        # Inquire as to the status of the account
        resp = actions.submit_inquiry(source)
        self.assertEqual(resp.balance, Decimal('0.00'))
        self.assertEqual(resp.open_to_buy, Decimal('5000.00'))


    @mock.patch('soap.get_transport')
    def test_submit_inquiry_failure(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(self._get_failed_response())

        source = self._build_account('9999999999999990')
        # Account is invalid
        def submit():
            actions.submit_inquiry(source)
        self.assertRaises(ValidationError, submit)


    def _get_success_response(self):
        resp = b"""<?xml version="1.0" encoding="utf-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <soapenv:Body>
                    <ns1:submitInquiryResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="http://services.webservices.retaildealer.wff.com">
                        <submitInquiryReturn>
                            <accountBalance>0.0</accountBalance>
                            <address>123 First Street</address>
                            <dealerId/>
                            <faults xsi:nil="true"/>
                            <firstName>John</firstName>
                            <lastName>Smith</lastName>
                            <lastPayment>0.0</lastPayment>
                            <lastPaymentDate>000000  </lastPaymentDate>
                            <merchantNumber>111111111111116</merchantNumber>
                            <middleInitial>Q</middleInitial>
                            <openToBuy>5000.0</openToBuy>
                            <paymentDue>0.0</paymentDue>
                            <paymentDueDate>000000  </paymentDueDate>
                            <phone>5559998888</phone>
                            <retailerAccountNumber>9999999999999991</retailerAccountNumber>
                            <sorErrorDescription/>
                            <systemCode>000</systemCode>
                            <terminalNumber>0000</terminalNumber>
                            <transactionCode>8</transactionCode>
                            <transactionStatus>I0</transactionStatus>
                            <uuid>7500b612-2154-11e6-b69e-0242ac110003</uuid>
                            <wfAccountNumber>9999999999999991</wfAccountNumber>
                        </submitInquiryReturn>
                    </ns1:submitInquiryResponse>
                </soapenv:Body>
            </soapenv:Envelope>"""
        return resp


    def _get_failed_response(self):
        resp = b"""<?xml version="1.0" encoding="utf-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <soapenv:Body>
                    <ns1:submitInquiryResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="http://services.webservices.retaildealer.wff.com">
                        <submitInquiryReturn>
                            <accountBalance>0.0</accountBalance>
                            <address/>
                            <dealerId/>
                            <faults xsi:nil="true"/>
                            <firstName/>
                            <lastName/>
                            <lastPayment>0.0</lastPayment>
                            <lastPaymentDate>000000  </lastPaymentDate>
                            <merchantNumber>111111111111116</merchantNumber>
                            <middleInitial/>
                            <openToBuy>0.0</openToBuy>
                            <paymentDue>0.0</paymentDue>
                            <paymentDueDate>000000  </paymentDueDate>
                            <phone>0000000000</phone>
                            <retailerAccountNumber>9999999999999990</retailerAccountNumber>
                            <sorErrorDescription>DEMO INVALID ACCOUNT</sorErrorDescription>
                            <systemCode>000</systemCode>
                            <terminalNumber>0000</terminalNumber>
                            <transactionCode>8</transactionCode>
                            <transactionStatus>I1</transactionStatus>
                            <uuid>74de5f22-2154-11e6-b69e-0242ac110003</uuid>
                            <wfAccountNumber>9999999999999990</wfAccountNumber>
                        </submitInquiryReturn>
                    </ns1:submitInquiryResponse>
                </soapenv:Body>
            </soapenv:Envelope>"""
        return resp



class CreditApplicationTest(BaseTest):
    @mock.patch('soap.get_transport')
    def test_us_submit_single(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(self._get_success_response())

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
        get_transport.return_value = self._build_transport_with_reply(self._get_success_response())

        app = self._build_us_join_credit_app('999999990', '999999990')
        self.assertTrue(app.is_joint)

        resp = actions.submit_credit_application(app)
        self.assertEqual(resp.transaction_status, CREDIT_APP_APPROVED)
        self.assertEqual(resp.account_number, '9999999999999999')
        self.assertEqual(resp.credit_limit, Decimal('7500.00'))


    @mock.patch('soap.get_transport')
    def test_missing_ssn(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(self._get_invalid_ssn_response())

        app = self._build_us_single_credit_app(None)
        def submit():
            actions.submit_credit_application(app)
        self.assertRaises(ValidationError, submit)


    @mock.patch('soap.get_transport')
    def test_submit_denied(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(self._get_denied_response())

        app = self._build_us_single_credit_app('999999994')
        def submit():
            actions.submit_credit_application(app)
        self.assertRaises(CreditApplicationDenied, submit)


    def _get_success_response(self):
        resp = b"""<?xml version="1.0" encoding="utf-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <soapenv:Body>
                    <ns1:submitCreditAppResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="http://v1.services.webservices.retaildealer.wff.com">
                        <submitCreditAppReturn>
                            <authorizationNumber>000000</authorizationNumber>
                            <authorizedAmount>0.0</authorizedAmount>
                            <creditLimit>7500.0</creditLimit>
                            <dealerId/>
                            <faults xsi:nil="true"/>
                            <fieldInError1>0000</fieldInError1>
                            <fieldInError2>0000</fieldInError2>
                            <fieldInError3>0000</fieldInError3>
                            <fieldInError4>0000</fieldInError4>
                            <fieldInError5>0000</fieldInError5>
                            <merchantNumber>111111111111116</merchantNumber>
                            <retailerAccountNumber/>
                            <sorErrorDescription/>
                            <systemCode>000</systemCode>
                            <terminalNumber>0000</terminalNumber>
                            <transactionCode>A6</transactionCode>
                            <transactionStatus>E0</transactionStatus>
                            <uuid>21fa5918-2155-11e6-8b70-0242ac110003</uuid>
                            <wfAccountNumber>9999999999999999</wfAccountNumber>
                        </submitCreditAppReturn>
                    </ns1:submitCreditAppResponse>
                </soapenv:Body>
            </soapenv:Envelope>"""
        return resp


    def _get_invalid_ssn_response(self):
        resp = b"""<?xml version="1.0" encoding="utf-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <soapenv:Body>
                    <ns1:submitCreditAppResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="http://v1.services.webservices.retaildealer.wff.com">
                        <submitCreditAppReturn>
                            <authorizationNumber xsi:nil="true"/>
                            <authorizedAmount xsi:nil="true"/>
                            <creditLimit xsi:nil="true"/>
                            <dealerId xsi:nil="true"/>
                            <faults soapenc:arrayType="ns2:WFFIFault[1]" xmlns:ns2="http://faults.webservices.retaildealer.wff.com" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xsi:type="soapenc:Array">
                                <faults>
                                    <adviceText/>
                                    <faultActor>WFFServices/RetailResponse</faultActor>
                                    <faultCodeAsString>RWS3020</faultCodeAsString>
                                    <faultDetailString>Please supply a valid main applicant SSN.</faultDetailString>
                                    <faultReason/>
                                    <faultString>RWS_INVALID_MAIN_SSN</faultString>
                                </faults>
                            </faults>
                            <fieldInError1 xsi:nil="true"/>
                            <fieldInError2 xsi:nil="true"/>
                            <fieldInError3 xsi:nil="true"/>
                            <fieldInError4 xsi:nil="true"/>
                            <fieldInError5 xsi:nil="true"/>
                            <merchantNumber>111111111111116</merchantNumber>
                            <retailerAccountNumber xsi:nil="true"/>
                            <sorErrorDescription xsi:nil="true"/>
                            <systemCode xsi:nil="true"/>
                            <terminalNumber xsi:nil="true"/>
                            <transactionCode>A6</transactionCode>
                            <transactionStatus xsi:nil="true"/>
                            <uuid>7a1098b0-2155-11e6-a236-0242ac110003</uuid>
                            <wfAccountNumber xsi:nil="true"/>
                        </submitCreditAppReturn>
                    </ns1:submitCreditAppResponse>
                </soapenv:Body>
            </soapenv:Envelope>"""
        return resp


    def _get_denied_response(self):
        resp = b"""<?xml version="1.0" encoding="utf-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <soapenv:Body>
                    <ns1:submitCreditAppResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="http://v1.services.webservices.retaildealer.wff.com">
                        <submitCreditAppReturn>
                            <authorizationNumber>000000</authorizationNumber>
                            <authorizedAmount>0.0</authorizedAmount>
                            <creditLimit>0.0</creditLimit>
                            <dealerId/>
                            <faults xsi:nil="true"/>
                            <fieldInError1>0000</fieldInError1>
                            <fieldInError2>0000</fieldInError2>
                            <fieldInError3>0000</fieldInError3>
                            <fieldInError4>0000</fieldInError4>
                            <fieldInError5>0000</fieldInError5>
                            <merchantNumber>111111111111116</merchantNumber>
                            <retailerAccountNumber/>
                            <sorErrorDescription/>
                            <systemCode>000</systemCode>
                            <terminalNumber>0000</terminalNumber>
                            <transactionCode>A6</transactionCode>
                            <transactionStatus>E4</transactionStatus>
                            <uuid>aa962252-2155-11e6-8512-0242ac110003</uuid>
                            <wfAccountNumber>0000089999999999</wfAccountNumber>
                        </submitCreditAppReturn>
                    </ns1:submitCreditAppResponse>
                </soapenv:Body>
            </soapenv:Envelope>"""
        return resp