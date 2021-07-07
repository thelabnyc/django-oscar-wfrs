from ..core.constants import (
    TRANS_APPROVED,
    TRANS_TYPE_AUTH,
    TRANS_TYPE_CANCEL_AUTH,
    # TRANS_TYPE_CHARGE,
    # TRANS_TYPE_AUTH_AND_CHARGE,
    TRANS_TYPE_AUTH_AND_CHARGE_TIMEOUT_REVERSAL,
    TRANS_TYPE_RETURN_CREDIT,
    TRANS_TYPE_VOID_SALE,
    TRANS_TYPE_VOID_RETURN,
)
from wellsfargo.core.exceptions import TransactionDenied
from ..models import APIMerchantNum, FinancingPlan, TransferMetadata
from ..utils import as_decimal
from .client import WFRSGatewayAPIClient
import uuid


class TransactionsAPIClient(WFRSGatewayAPIClient):
    def __init__(self, current_user=None):
        self.current_user = current_user

    def submit_transaction(self, trans_request, transaction_uuid=None, persist=True):
        api_path = self.get_api_path(trans_request)
        creds = APIMerchantNum.get_for_user(self.current_user)
        # Submit transaction to WFRS
        trans_request_data = {
            "locale": trans_request.locale,
            "authorization_number": trans_request.auth_number,
            "account_number": trans_request.account_number,
            "plan_number": str(trans_request.plan_number),
            "amount": str(trans_request.amount),
            "ticket_number": trans_request.ticket_number,
            "merchant_number": creds.merchant_num,
        }
        if transaction_uuid is None:
            transaction_uuid = uuid.uuid4()
        resp = self.api_post(
            api_path, client_request_id=transaction_uuid, json=trans_request_data
        )
        resp.raise_for_status()
        resp_data = resp.json()
        # Find the related plan
        plan_number = resp_data.get("plan_number", trans_request.plan_number)
        plan, _ = FinancingPlan.objects.get_or_create(plan_number=plan_number)
        # Persist transaction data and WF specific metadata
        transfer = TransferMetadata()
        transfer.user = trans_request.user
        transfer.merchant_name = creds.name
        transfer.merchant_num = creds.merchant_num
        transfer.account_number = resp_data.get(
            "account_number", trans_request.account_number
        )
        transfer.merchant_reference = transaction_uuid
        transfer.amount = as_decimal(resp_data.get("amount", trans_request.amount))
        transfer.type_code = trans_request.type_code
        transfer.ticket_number = resp_data.get(
            "ticket_number", trans_request.ticket_number
        )
        transfer.financing_plan = plan
        transfer.auth_number = resp_data.get(
            "authorization_number", trans_request.auth_number
        )
        transfer.status = resp_data["transaction_status"]
        transfer.message = resp_data.get("status_message", "")
        transfer.disclosure = resp_data.get("disclosure", "")
        if persist:
            transfer.save()
        # Check for approval
        if transfer.status != TRANS_APPROVED:
            exc = TransactionDenied("%s: %s" % (transfer.status, transfer.message))
            exc.status = transfer.status
            raise exc
        # Return the transfer metadata
        return transfer

    def get_api_path(self, trans_request):
        actions = {
            TRANS_TYPE_AUTH: "authorization",
            TRANS_TYPE_CANCEL_AUTH: "cancel-authorization",
            # TRANS_TYPE_CHARGE: 'charge',
            # TRANS_TYPE_AUTH_AND_CHARGE: 'authorization-charge',
            TRANS_TYPE_AUTH_AND_CHARGE_TIMEOUT_REVERSAL: "timeout-authorization-charge",
            TRANS_TYPE_RETURN_CREDIT: "return",
            TRANS_TYPE_VOID_SALE: "void-sale",
            TRANS_TYPE_VOID_RETURN: "void-return",
        }
        action = actions.get(trans_request.type_code)
        if action is None:
            raise ValueError("Unexpected transaction type: %s" % action)
        api_path = "/credit-cards/private-label/new-accounts/v2/payment/transactions/{action}".format(
            action=action
        )
        return api_path
