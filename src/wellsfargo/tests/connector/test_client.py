from urllib.parse import parse_qs
from django.core.cache import cache
from django.test import TestCase
from wellsfargo.connector.client import WFRSGatewayAPIClient
import requests_mock


class WFRSGatewayAPIClientTest(TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    @requests_mock.Mocker()
    def test_get_api_key(self, rmock):
        call_count = {
            "i": 0,
        }

        # Setup mock for generating a token
        def match_request(request):
            # Check auth header
            self.assertTrue(request.headers["Authorization"].startswith("Basic "))
            # Check data in body
            data = parse_qs(request.body)
            self.assertEqual(
                data,
                {
                    "grant_type": [
                        "client_credentials",
                    ],
                    "scope": [
                        " ".join(
                            [
                                "PLCCA-Prequalifications",
                                "PLCCA-Applications",
                                "PLCCA-Payment-Calculations",
                                "PLCCA-Transactions-Authorization",
                                "PLCCA-Transactions-Charge",
                                "PLCCA-Transactions-Authorization-Charge",
                                "PLCCA-Transactions-Return",
                                "PLCCA-Transactions-Cancel-Authorization",
                                "PLCCA-Transactions-Void-Return",
                                "PLCCA-Transactions-Void-Sale",
                                "PLCCA-Transactions-Timeout-Authorization-Charge",
                                "PLCCA-Transactions-Timeout-Return",
                                "PLCCA-Account-Details",
                            ]
                        ),
                    ],
                },
            )
            # Increment call count
            call_count["i"] += 1
            return True

        # Register request mock
        rmock.post(
            "https://api-sandbox.wellsfargo.com/token",
            additional_matcher=match_request,
            json={
                "access_token": "16a05f65dd41569af67dbdca7ea4da4d",
                "scope": "",
                "token_type": "Bearer",
                "expires_in": 79900,
            },
        )

        self.assertEqual(call_count["i"], 0)

        # Get a token
        token = WFRSGatewayAPIClient().get_api_key()
        self.assertEqual(token.api_key, "16a05f65dd41569af67dbdca7ea4da4d")
        self.assertEqual(token.is_expired, False)
        self.assertEqual(call_count["i"], 1)

        # Get token again
        token = WFRSGatewayAPIClient().get_api_key()
        self.assertEqual(token.api_key, "16a05f65dd41569af67dbdca7ea4da4d")
        self.assertEqual(token.is_expired, False)
        self.assertEqual(call_count["i"], 1)
