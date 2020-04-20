from ..core.constants import (
    PREQUAL_TRANS_CODE_MERCHANT_HOSTED_ONLINE,
    PREQUAL_TRANS_STATUS_ERROR,
    PREQUAL_CUSTOMER_RESP_NONE,
)
from ..models import APIMerchantNum, PreQualificationResponse
from ..utils import as_decimal, format_phone, remove_null_dict_keys
from .client import WFRSGatewayAPIClient
import logging
import urllib.parse

logger = logging.getLogger(__name__)


class PrequalAPIClient(WFRSGatewayAPIClient):

    def __init__(self, current_user=None):
        self.current_user = current_user


    def check_prescreen_status(self, prequal_request):
        creds = APIMerchantNum.get_for_user(self.current_user)
        # Build request data
        request_data = {
            "merchant_number": creds.merchant_num,
            "transaction_code": PREQUAL_TRANS_CODE_MERCHANT_HOSTED_ONLINE,
            "main_applicant": {
                "first_name": prequal_request.first_name,
                "middle_initial": prequal_request.middle_initial,
                "last_name": prequal_request.last_name,
                "phone_number": format_phone(prequal_request.phone),
                "email": prequal_request.email,
                "last_four_ssn": None,
                "address": {
                    "address_line_1": prequal_request.line1,
                    "address_line_2": prequal_request.line2,
                    "city": prequal_request.city,
                    "state_code": prequal_request.state,
                    "postal_code": prequal_request.postcode,
                },
            },
            "entry_point": prequal_request.entry_point,
            "requested_credit_limit": None,
        }
        request_data = remove_null_dict_keys(request_data)
        # Save the credentials used to make the request
        prequal_request.merchant_name = creds.name
        prequal_request.merchant_num = creds.merchant_num
        prequal_request.save()
        # Send the request to WF
        resp = self.api_post('/credit-cards/private-label/new-accounts/v2/prequalifications',
            client_request_id=prequal_request.uuid,
            json=request_data)
        resp.raise_for_status()
        resp_data = resp.json()
        # Save the pre-qualification response data
        response = PreQualificationResponse()
        response.request = prequal_request
        response.status = resp_data.get('decision_status', PREQUAL_TRANS_STATUS_ERROR)
        response.message = resp_data.get('decision_message', '')
        response.offer_indicator = resp_data.get('offer_indicator', '')
        response.credit_limit = as_decimal(resp_data.get('max_credit_limit', '0.00'))
        response.response_id = resp_data.get('application_id', '')
        response.application_url = urllib.parse.unquote(resp_data.get('URL', ''))
        response.customer_response = PREQUAL_CUSTOMER_RESP_NONE
        response.save()
        return response
