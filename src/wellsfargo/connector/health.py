from .client import WFRSGatewayAPIClient



class HealthCheckAPIClient(WFRSGatewayAPIClient):

    def check_credentials(self):
        resp = self.api_get('/utilities/v1/hello-wellsfargo')
        resp.raise_for_status()
        return resp.json()['response']
