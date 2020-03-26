from ..core.constants import (
    PREQUAL_CUSTOMER_RESP_NONE,
)
from ..models import APICredentials, PreQualificationResponse
from ..utils import as_decimal
from .client import WFRSGatewayAPIClient
import logging

logger = logging.getLogger(__name__)


class PrescreenAPIClient(WFRSGatewayAPIClient):

    def __init__(self, current_user=None):
        self.current_user = current_user


    def check_prescreen_status(self, prequal_request):
        creds = APICredentials.get_credentials(self.current_user)
        # Build request data
        request_data = {
            "main_applicant": {
                "address": {
                    "address_line_1": prequal_request.line1,
                    "city": prequal_request.city,
                    "state_code": prequal_request.state,
                    "postal_code": prequal_request.postcode,
                },
                "first_name": prequal_request.first_name,
                "last_name": prequal_request.last_name,
                "email": prequal_request.email,
                "last_four_ssn": "9999",
            },
            "merchant_number": creds.merchant_num,
            "transaction_code": "MAH",
            "entry_point": prequal_request.entry_point,
        }
        print(request_data)
        # Save the credentials used to make the request
        prequal_request.merchant_name = creds.name
        prequal_request.merchant_num = creds.merchant_num
        prequal_request.credentials = creds
        prequal_request.save()
        # Send the request to WF
        resp = self.api_post('/credit-cards/private-label/new-accounts/v2/prequalifications',
            client_request_id=prequal_request.uuid,
            json=request_data)
        print(resp.text)
        resp.raise_for_status()
        resp_data = resp.json()
        print(resp_data)
        # Sanity check the response
        if resp_data.get('decision_status') is None or resp_data.get('application_id') is None:
            logger.info('WFRS pre-qualification request return null data for pre-request[{}]'.format(prequal_request.pk))
            return None
        # Save the pre-qualification response data
        response = PreQualificationResponse()
        response.request = prequal_request
        response.response_id = resp_data['application_id']
        response.status = resp_data['decision_status']
        response.message = resp_data.get('decision_message', '')
        response.credit_limit = as_decimal(resp_data.get('max_credit_limit', '0.00'))
        # response.offer_indicator = ''
        # response.application_url = urllib.parse.unquote(resp.url or '')
        response.customer_response = PREQUAL_CUSTOMER_RESP_NONE
        response.save()
        return response
