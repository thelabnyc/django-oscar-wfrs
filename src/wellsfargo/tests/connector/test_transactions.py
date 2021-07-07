from decimal import Decimal
from wellsfargo.core.constants import TRANS_APPROVED
from wellsfargo.core.structures import TransactionRequest
from wellsfargo.core.exceptions import TransactionDenied
from wellsfargo.connector.transactions import TransactionsAPIClient
from wellsfargo.models import FinancingPlan
from wellsfargo.tests.base import BaseTest
import requests_mock
import json


class TransactionsAPIClientTest(BaseTest):
    @requests_mock.Mocker()
    def test_submit_transaction_success(self, rmock):
        plan = FinancingPlan.objects.create(
            plan_number="9999", description="", apr=0, term_months=0
        )

        self.mock_get_api_token_request(rmock)

        def match_submit_transaction(request):
            # Check auth header
            self.assertTrue(request.headers["Authorization"].startswith("Bearer "))
            # Check data in body
            data = json.loads(request.body)
            self.assertEqual(
                data,
                {
                    "locale": "en_US",
                    "authorization_number": "000000",
                    "account_number": "9999999999999991",
                    "plan_number": "9999",
                    "amount": "2159.99",
                    "ticket_number": "1234567890",
                    "merchant_number": "1111111111111111",
                },
            )
            return True

        self.mock_successful_transaction_request(
            rmock, additional_matcher=match_submit_transaction
        )

        # Authorize a change against the credit line
        request = TransactionRequest()
        request.user = self.joe
        request.account_number = "9999999999999991"
        request.plan_number = plan.plan_number
        request.amount = Decimal("2159.99")
        request.ticket_number = "1234567890"

        transfer = TransactionsAPIClient().submit_transaction(
            request, transaction_uuid="c17381a3-22fa-4463-8b0a-a3c18f6c4a44"
        )

        # Should return a valid transfer object
        self.assertEqual(transfer.user, self.joe)
        self.assertEqual(transfer.merchant_name, self.credentials.name)
        self.assertEqual(transfer.merchant_num, self.credentials.merchant_num)
        self.assertEqual(
            transfer.merchant_reference, "c17381a3-22fa-4463-8b0a-a3c18f6c4a44"
        )
        self.assertEqual(transfer.amount, Decimal("2159.99"))
        self.assertEqual(transfer.type_code, "5")
        self.assertEqual(transfer.ticket_number, "123444")
        self.assertEqual(transfer.financing_plan.plan_number, 9999)
        self.assertEqual(transfer.auth_number, "000000")
        self.assertEqual(transfer.status, TRANS_APPROVED)
        self.assertEqual(transfer.message, "APPROVED: 123434")
        self.assertEqual(
            transfer.disclosure,
            "REGULAR TERMS WITH REGULAR PAYMENTS. THE REGULAR RATE IS 28.99%.",
        )

    @requests_mock.Mocker()
    def test_submit_transaction_denied(self, rmock):
        plan = FinancingPlan.objects.create(
            plan_number="9999", description="", apr=0, term_months=0
        )

        self.mock_get_api_token_request(rmock)

        def match_submit_transaction(request):
            # Check auth header
            self.assertTrue(request.headers["Authorization"].startswith("Bearer "))
            # Check data in body
            data = json.loads(request.body)
            self.assertEqual(
                data,
                {
                    "locale": "en_US",
                    "authorization_number": "000000",
                    "account_number": "9999999999999991",
                    "plan_number": "9999",
                    "amount": "2159.99",
                    "ticket_number": "1234567890",
                    "merchant_number": "1111111111111111",
                },
            )
            return True

        self.mock_declined_transaction_request(
            rmock, additional_matcher=match_submit_transaction
        )

        # Authorize a change against the credit line
        request = TransactionRequest()
        request.user = self.joe
        request.account_number = "9999999999999991"
        request.plan_number = plan.plan_number
        request.amount = Decimal("2159.99")
        request.ticket_number = "1234567890"

        with self.assertRaises(TransactionDenied):
            TransactionsAPIClient().submit_transaction(
                request, transaction_uuid="c17381a3-22fa-4463-8b0a-a3c18f6c4a44"
            )
