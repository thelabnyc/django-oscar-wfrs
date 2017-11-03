from suds.wsse import Security, UsernameToken
from ..models import FraudScreenResult
import soap
import logging
import uuid

logger = logging.getLogger(__name__)

try:
    from cybersource.constants import CHECKOUT_FINGERPRINT_SESSION_ID
except ImportError:
    logger.warning('Please install django-oscar-cybersource when using wellsfargo.fraud.cybersource.DecisionManagerFraudProtection.')
    CHECKOUT_FINGERPRINT_SESSION_ID = None


class DecisionManagerFraudProtection(object):
    """
    Screen Transactions for Fraud using the via Cybersource Decision Manager and the Simple Order API.

    See Cybersource's `API Docs <https://www.cybersource.com/developers/getting_started/integration_methods/simple_order_api/>`_.

    Usage:

    WFRS_FRAUD_PROTECTION = {
        'fraud_protection': 'wellsfargo.fraud.cybersource.DecisionManagerFraudProtection',
        'fraud_protection_kwargs': {
            'wsdl': 'https://ics2wstesta.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.141.wsdl',
            'merchant_id': 'myMerchantID',
            'transaction_security_key': 'fooooo==',
        }
    }

    The given WSDL should be one of the following:

    - Test Environments: ``https://ics2wstesta.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.141.wsdl``
    - Production Environments: ``https://ics2wsa.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.141.wsdl``

    MerchantID should be your Cybersource account's merchant ID. Transaction security key should be a SOAP Toolkit API Security
    Keys. You can make find this in the Cybersource Business Center => Transaction Security Keys => Security Keys for the SOAP
    Toolkit API => Generate Key. It is be secret and not be checked into source-control. Treat this like a password.
    """
    SCREEN_TYPE_NAME = 'Cybersource'


    def __init__(self, wsdl, merchant_id, transaction_security_key, soap_log_prefix='CYBERSOURCE'):
        self.merchant_id = merchant_id

        # Build a SOAP client
        self.client = soap.get_client(wsdl, soap_log_prefix)

        # Add WSSE Security Header to client
        security = Security()
        token = UsernameToken(self.merchant_id, transaction_security_key)
        security.tokens.append(token)
        self.client.set_options(wsse=security)


    def screen_transaction(self, request, order):
        data = {}

        # Run the Advanced Fraud Screen Service
        data['afsService'] = self.client.factory.create('ns0:AFSService')
        data['afsService']._run = "true"

        # Add in request and merchant data
        if CHECKOUT_FINGERPRINT_SESSION_ID and request.session.get(CHECKOUT_FINGERPRINT_SESSION_ID):
            data['deviceFingerprintID'] = request.session[CHECKOUT_FINGERPRINT_SESSION_ID]
        data['merchantID'] = self.merchant_id
        data['merchantReferenceCode'] = order.number

        # Add order customer data
        data['billTo'] = self.client.factory.create('ns0:BillTo')
        data['billTo'].email = order.email
        data['billTo'].ipAddress = request.META.get('REMOTE_ADDR')
        if order.user:
            data['billTo'].customerID = order.user.pk

        # Add order billing data
        if order.billing_address:
            data['billTo'].firstName = order.billing_address.first_name
            data['billTo'].lastName = order.billing_address.last_name
            data['billTo'].street1 = order.billing_address.line1
            data['billTo'].street2 = order.billing_address.line2
            data['billTo'].city = order.billing_address.line4
            data['billTo'].state = order.billing_address.state
            data['billTo'].postalCode = order.billing_address.postcode
            data['billTo'].country = order.billing_address.country.iso_3166_1_a2

        # Add order shipping data
        if order.shipping_address:
            data['shipTo'] = self.client.factory.create('ns0:ShipTo')
            data['shipTo'].phoneNumber = order.shipping_address.phone_number
            data['shipTo'].firstName = order.shipping_address.first_name
            data['shipTo'].lastName = order.shipping_address.last_name
            data['shipTo'].street1 = order.shipping_address.line1
            data['shipTo'].street2 = order.shipping_address.line2
            data['shipTo'].city = order.shipping_address.line4
            data['shipTo'].state = order.shipping_address.state
            data['shipTo'].postalCode = order.shipping_address.postcode
            data['shipTo'].country = order.shipping_address.country.iso_3166_1_a2

        # Add order total data
        data['purchaseTotals'] = self.client.factory.create('ns0:PurchaseTotals')
        data['purchaseTotals'].currency = order.currency
        data['purchaseTotals'].grandTotalAmount = order.total_incl_tax

        # Send the transaction to Cybersource to process
        try:
            resp = self.client.service.runTransaction(**data)
        except Exception:
            logger.exception("Failed to run Cybersource Advanced Fraud Screen Service on Order {}".format(order.number))
            resp = None

        # Parse the response for a decision code and a message
        try:
            decision, message = self.parse_response_outcome(resp)
        except Exception:
            decision, message = FraudScreenResult.DECISION_ERROR, "Error: Could not parse Cybersource response."

        # Get the transaction ID so that decision manager transactions can be traced through to Wells Fargo transactions
        try:
            reference = resp.requestID
        except Exception:
            reference = uuid.uuid1()

        # Save the result of the fraud screen
        result = FraudScreenResult()
        result.screen_type = self.SCREEN_TYPE_NAME
        result.order = order
        result.reference = reference
        result.decision = decision
        result.message = message
        result.save()

        # Return the FraudScreenResult instance
        return result


    def parse_response_outcome(self, resp):
        # Accept
        if resp.reasonCode == 100:
            return FraudScreenResult.DECISION_ACCEPT, "Transaction accepted. Reason code {}".format(resp.reasonCode)

        # Review
        if resp.reasonCode == 480:
            return FraudScreenResult.DECISION_REVIEW, "The order is marked for review by Decision Manager. Reason code {}".format(resp.reasonCode)

        # Errors
        if resp.reasonCode == 101:
            return FraudScreenResult.DECISION_ERROR, "The request is missing one or more required fields. Reason code {}".format(resp.reasonCode)

        if resp.reasonCode == 102:
            return FraudScreenResult.DECISION_ERROR, "One or more fields in the request contains invalid data. Reason code {}".format(resp.reasonCode)

        if resp.reasonCode == 150:
            return FraudScreenResult.DECISION_ERROR, "Error: General system failure. Reason code {}".format(resp.reasonCode)

        if resp.reasonCode == 151:
            return FraudScreenResult.DECISION_ERROR, "Error: The request was received but there was a server time-out. Reason code {}".format(resp.reasonCode)

        if resp.reasonCode == 152:
            return FraudScreenResult.DECISION_ERROR, "Error: The request was received but there was a service time-out. Reason code {}".format(resp.reasonCode)

        # Rejections
        if resp.reasonCode == 202:
            return FraudScreenResult.DECISION_REJECT, "CyberSource declined the request because the card has expired. Reason code {}".format(resp.reasonCode)

        if resp.reasonCode == 231:
            return FraudScreenResult.DECISION_REJECT, "The account number is invalid. Reason code {}".format(resp.reasonCode)

        if resp.reasonCode == 234:
            return FraudScreenResult.DECISION_REJECT, "There is a problem with your CyberSource merchant configuration. Reason code {}".format(resp.reasonCode)

        if resp.reasonCode == 400:
            return FraudScreenResult.DECISION_REJECT, "The fraud score exceeds your threshold. Reason code {}".format(resp.reasonCode)

        if resp.reasonCode == 481:
            return FraudScreenResult.DECISION_REJECT, "The order is rejected by Decision Manager. Reason code {}".format(resp.reasonCode)

        # If we don't recognize the reasonCode, go by the decision field
        if resp.decision == 'ACCEPT':
            return FraudScreenResult.DECISION_ACCEPT, "Transaction accepted. Decision is {}".format(resp.decision)

        if resp.decision == 'ERROR':
            return FraudScreenResult.DECISION_ERROR, "An unknown error occurred. Decision is {}".format(resp.decision)

        if resp.decision == 'REJECT':
            return FraudScreenResult.DECISION_REJECT, "Transaction rejected. Decision is {}".format(resp.decision)

        if resp.decision == 'REVIEW':
            return FraudScreenResult.DECISION_REVIEW, "Transaction flagged for review. Decision is {}".format(resp.decision)

        # Catch-all
        return FraudScreenResult.DECISION_ERROR, "Error: Could not parse Cybersource response."
