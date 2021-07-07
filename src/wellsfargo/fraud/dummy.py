from ..models import FraudScreenResult
import logging
import uuid

logger = logging.getLogger(__name__)


class DummyFraudProtection(object):
    """
    Implements Wells Fargo Fraud Protection interface, but doesn't actually check anything. It just approves everything.

    Usage:

    WFRS_FRAUD_PROTECTION = {
        'fraud_protection': 'wellsfargo.fraud.dummy.DummyFraudProtection',
    }
    """

    SCREEN_TYPE_NAME = "Dummy"

    def __init__(self, decision=None, message=None):
        self.decision = decision or FraudScreenResult.DECISION_ACCEPT
        self.message = message or "Transaction accepted."

    def screen_transaction(self, request, order):
        result = FraudScreenResult()
        result.screen_type = self.SCREEN_TYPE_NAME
        result.order = order
        result.reference = str(uuid.uuid1())
        result.decision = self.decision
        result.message = self.message
        result.save()
        return result
