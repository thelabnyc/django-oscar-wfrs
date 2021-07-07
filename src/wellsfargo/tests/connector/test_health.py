from wellsfargo.connector.health import HealthCheckAPIClient
from wellsfargo.tests.base import BaseTest
import requests_mock


class HealthCheckAPIClientTest(BaseTest):
    @requests_mock.Mocker()
    def test_check_credentials(self, rmock):
        self.mock_get_api_token_request(rmock)

        rmock.get(
            "https://api-sandbox.wellsfargo.com/utilities/v1/hello-wellsfargo",
            json={
                "response": "Congratulations! Your environment is set up correctly. Thank you for your business.",
            },
        )
        # Hit the health check endpoint
        resp = HealthCheckAPIClient().check_credentials()
        self.assertEquals(
            resp,
            "Congratulations! Your environment is set up correctly. Thank you for your business.",
        )
