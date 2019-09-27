from django.test import TestCase, RequestFactory
from oscar.test.factories import create_order
from soap.tests import SoapTest
from wellsfargo.fraud import screen_transaction, WFRS_FRAUD_PROTECTION
from wellsfargo.tests import responses
from unittest import mock



def patch_fraud_protection(klass, **klass_kwargs):
    def decorate(fn):
        def wrapper(*args, **kwargs):
            _old_klass = WFRS_FRAUD_PROTECTION['fraud_protection']
            _old_klass_kwargs = WFRS_FRAUD_PROTECTION['fraud_protection_kwargs']
            WFRS_FRAUD_PROTECTION['fraud_protection'] = klass
            WFRS_FRAUD_PROTECTION['fraud_protection_kwargs'] = klass_kwargs
            resp = fn(*args, **kwargs)
            WFRS_FRAUD_PROTECTION['fraud_protection'] = _old_klass
            WFRS_FRAUD_PROTECTION['fraud_protection_kwargs'] = _old_klass_kwargs
            return resp
        return wrapper
    return decorate



class FraudScreenFacadeTest(TestCase):

    @patch_fraud_protection('wellsfargo.fraud.dummy.DummyFraudProtection')
    def test_facade(self):
        request = RequestFactory().get('/api/checkout/')
        order = create_order()
        result = screen_transaction(request, order)

        self.assertEqual(result.screen_type, 'Dummy')
        self.assertEqual(result.order, order)
        self.assertEqual(result.decision, 'ACCEPT')
        self.assertEqual(result.message, 'Transaction accepted.')



class DecisionManagerFraudProtectionTest(SoapTest, TestCase):
    KWARGS = {
        'wsdl': 'https://ics2wstesta.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.141.wsdl',
        'merchant_id': 'mymerchantid',
        'transaction_security_key': 'mysoappassword',
    }

    @patch_fraud_protection('wellsfargo.fraud.cybersource.DecisionManagerFraudProtection', **KWARGS)
    @mock.patch('soap.get_transport')
    def test_decision_manager_accept(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.cybersource_accept)

        request = RequestFactory().get('/api/checkout/')
        order = create_order()
        result = screen_transaction(request, order)

        self.assertEqual(result.screen_type, 'Cybersource')
        self.assertEqual(result.order, order)
        self.assertEqual(result.decision, 'ACCEPT')
        self.assertEqual(result.message, 'Transaction accepted. Reason code 100')


    @patch_fraud_protection('wellsfargo.fraud.cybersource.DecisionManagerFraudProtection', **KWARGS)
    @mock.patch('soap.get_transport')
    def test_decision_manager_review(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.cybersource_review)

        request = RequestFactory().get('/api/checkout/')
        order = create_order()
        result = screen_transaction(request, order)

        self.assertEqual(result.screen_type, 'Cybersource')
        self.assertEqual(result.order, order)
        self.assertEqual(result.decision, 'REVIEW')
        self.assertEqual(result.message, 'The order is marked for review by Decision Manager. Reason code 480')


    @patch_fraud_protection('wellsfargo.fraud.cybersource.DecisionManagerFraudProtection', **KWARGS)
    @mock.patch('soap.get_transport')
    def test_decision_manager_reject(self, get_transport):
        get_transport.return_value = self._build_transport_with_reply(responses.cybersource_reject)

        request = RequestFactory().get('/api/checkout/')
        order = create_order()
        result = screen_transaction(request, order)

        self.assertEqual(result.screen_type, 'Cybersource')
        self.assertEqual(result.order, order)
        self.assertEqual(result.decision, 'REJECT')
        self.assertEqual(result.message, 'The fraud score exceeds your threshold. Reason code 400')
