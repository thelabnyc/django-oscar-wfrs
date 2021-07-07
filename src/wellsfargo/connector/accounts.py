from ..models import (
    APIMerchantNum,
    AccountInquiryResult,
    CreditApplicationAddress,
)
from ..utils import as_decimal, remove_null_dict_keys
from .client import WFRSGatewayAPIClient
import logging
import uuid

logger = logging.getLogger(__name__)


class AccountsAPIClient(WFRSGatewayAPIClient):
    """
    Account Lookup Transaction Codes

    C1 – Includes first name, last name, and unique ID
    C2 – Includes any three of the following:
              - first name
              - last name
              - last 4 SSN
              - date of birth
              - postal code
              - phone
              - last 4 of acct number
    C4 – Only requires the account number
    """

    def __init__(self, current_user=None):
        self.current_user = current_user

    def lookup_account_by_prequal_offer_id(
        self, first_name, last_name, unique_id, **kwargs
    ):
        request_data = {
            "transaction_code": "C1",
            "first_name": first_name,
            "last_name": last_name,
            "unique_id": unique_id,
        }
        request_data.update(kwargs)
        return self._do_account_lookup(**request_data)

    def lookup_account_by_metadata(
        self,
        first_name=None,
        last_name=None,
        last_4_ssn=None,
        date_of_birth=None,
        postal_code=None,
        home_phone=None,
        last_4_account_number=None,
        **kwargs
    ):
        """
        Call must include at least 3 of the possible metadata items. For example, ``first_name`,
        ``last_name``, and ``postal_code``.
        """
        request_data = {
            "transaction_code": "C2",
            "first_name": first_name,
            "last_name": last_name,
            "last_4_ssn": last_4_ssn,
            "date_of_birth": date_of_birth,
            "postal_code": postal_code,
            "home_phone": home_phone,
            "last_4_account_number": last_4_account_number,
        }
        request_data.update(kwargs)
        return self._do_account_lookup(**request_data)

    def lookup_account_by_account_number(self, account_number, **kwargs):
        request_data = {
            "transaction_code": "C4",
            "account_number": account_number,
        }
        request_data.update(kwargs)
        return self._do_account_lookup(**request_data)

    def _do_account_lookup(self, **kwargs):
        # Assemble request data
        creds = APIMerchantNum.get_for_user(self.current_user)
        request_data = {
            "locale": "en_US",
            "merchant_number": creds.merchant_num,
        }
        request_data.update(kwargs)
        request_data = remove_null_dict_keys(request_data)
        # Apply formatting
        if "date_of_birth" in request_data:
            # Date of birth must be formatted as MMYY
            request_data["date_of_birth"] = request_data["date_of_birth"].strftime(
                "%m%y"
            )
        if "home_phone" in request_data:
            # Phone number be 10 digits, no groupings, no country code
            request_data["home_phone"] = str(request_data["home_phone"].national_number)
        # Send the request to WF
        resp = self.api_post(
            "/credit-cards/private-label/new-accounts/v2/details",
            client_request_id=uuid.uuid4(),
            json=request_data,
        )
        resp.raise_for_status()
        resp_data = resp.json()
        # Save main address from response
        main_applicant_address = None
        if resp_data.get("applicant", {}).get("address"):
            main_applicant_address = CreditApplicationAddress.objects.create(
                address_line_1=resp_data["applicant"]["address"].get("address_1", ""),
                address_line_2=resp_data["applicant"]["address"].get("address_2", ""),
                city=resp_data["applicant"]["address"].get("city", ""),
                state_code=resp_data["applicant"]["address"].get("state", ""),
                postal_code=resp_data["applicant"]["address"].get("postal_code", ""),
            )
        # Save joint address from response
        joint_applicant_address = None
        if resp_data.get("joint_applicant", {}).get("address"):
            joint_applicant_address = CreditApplicationAddress.objects.create(
                address_line_1=resp_data["joint_applicant"]["address"].get(
                    "address_1", ""
                ),
                address_line_2=resp_data["joint_applicant"]["address"].get(
                    "address_2", ""
                ),
                city=resp_data["joint_applicant"]["address"].get("city", ""),
                state_code=resp_data["joint_applicant"]["address"].get("state", ""),
                postal_code=resp_data["joint_applicant"]["address"].get(
                    "postal_code", ""
                ),
            )
        # Build response
        if not resp_data.get("account_number"):
            return None
        result = AccountInquiryResult()
        result.account_number = resp_data["account_number"]
        result.main_applicant_full_name = resp_data.get("applicant", {}).get("name")
        result.joint_applicant_full_name = resp_data.get("joint_applicant", {}).get(
            "name"
        )
        result.main_applicant_address = main_applicant_address
        result.joint_applicant_address = joint_applicant_address
        result.credit_limit = as_decimal(resp_data["credit_limit"])
        result.available_credit = as_decimal(resp_data["available_credit"])
        result.save()
        return result
