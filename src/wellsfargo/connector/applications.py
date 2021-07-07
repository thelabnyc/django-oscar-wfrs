from django.utils.translation import gettext as _
from ..core.constants import (
    CREDIT_APP_APPROVED,
    CREDIT_APP_PENDING,
)
from ..core.signals import wfrs_app_approved
from ..core.exceptions import (
    CreditApplicationDenied,
    CreditApplicationPending,
)
from ..models import (
    APIMerchantNum,
    AccountInquiryResult,
)
from ..utils import (
    as_decimal,
    format_date,
    format_phone,
    format_ssn,
    remove_null_dict_keys,
)
from .client import WFRSGatewayAPIClient
import uuid


class CreditApplicationsAPIClient(WFRSGatewayAPIClient):
    def __init__(self, current_user=None):
        self.current_user = current_user

    def submit_credit_application(self, credit_app):
        creds = APIMerchantNum.get_for_user(self.current_user)
        # Submit transaction to WFRS
        main_applicant = {
            "first_name": credit_app.main_applicant.first_name,
            "last_name": credit_app.main_applicant.last_name,
            "middle_initial": credit_app.main_applicant.middle_initial,
            "date_of_birth": format_date(credit_app.main_applicant.date_of_birth),
            "ssn": format_ssn(credit_app.main_applicant.ssn),
            "annual_income": credit_app.main_applicant.annual_income,
            "email_address": credit_app.main_applicant.email_address,
            "mobile_phone": format_phone(credit_app.main_applicant.mobile_phone),
            "home_phone": format_phone(credit_app.main_applicant.home_phone),
            "work_phone": format_phone(credit_app.main_applicant.work_phone),
            "employer_name": credit_app.main_applicant.employer_name,
            "housing_status": credit_app.main_applicant.housing_status,
            "address": {
                "address_line_1": credit_app.main_applicant.address.address_line_1,
                "address_line_2": credit_app.main_applicant.address.address_line_2,
                "city": credit_app.main_applicant.address.city,
                "state_code": credit_app.main_applicant.address.state_code,
                "postal_code": credit_app.main_applicant.address.postal_code,
            },
        }
        request_data = {
            "merchant_number": creds.merchant_num,
            "transaction_code": credit_app.transaction_code,
            "application_id": credit_app.application_id,
            "requested_credit_limit": credit_app.requested_credit_limit,
            "language_preference": credit_app.language_preference,
            "salesperson": credit_app.salesperson,
            "main_applicant": main_applicant,
        }
        # Add joint applicant (if there is one)
        if credit_app.joint_applicant:
            request_data["joint_applicant"] = {
                "first_name": credit_app.joint_applicant.first_name,
                "last_name": credit_app.joint_applicant.last_name,
                "middle_initial": credit_app.joint_applicant.middle_initial,
                "date_of_birth": format_date(credit_app.joint_applicant.date_of_birth),
                "ssn": format_ssn(credit_app.joint_applicant.ssn),
                "annual_income": credit_app.joint_applicant.annual_income,
                "email_address": credit_app.joint_applicant.email_address,
                "mobile_phone": format_phone(credit_app.joint_applicant.mobile_phone),
                "home_phone": format_phone(credit_app.joint_applicant.home_phone),
                "work_phone": format_phone(credit_app.joint_applicant.work_phone),
                "employer_name": credit_app.joint_applicant.employer_name,
                # "housing_status": credit_app.joint_applicant.housing_status,
                "address": {
                    "address_line_1": credit_app.joint_applicant.address.address_line_1,
                    "address_line_2": credit_app.joint_applicant.address.address_line_2,
                    "city": credit_app.joint_applicant.address.city,
                    "state_code": credit_app.joint_applicant.address.state_code,
                    "postal_code": credit_app.joint_applicant.address.postal_code,
                },
            }
        # Filter out null keys
        request_data = remove_null_dict_keys(request_data)
        # Submit application
        resp = self.api_post(
            "/credit-cards/private-label/new-accounts/v2/applications",
            client_request_id=uuid.uuid4(),
            json=request_data,
        )
        resp.raise_for_status()
        resp_data = resp.json()
        credit_app.merchant_name = creds.name
        credit_app.merchant_num = creds.merchant_num
        credit_app.status = resp_data["application_status"]
        credit_app.save()

        # If the status is not either Approved or Pending, it must be denied
        if resp_data["application_status"] not in (
            CREDIT_APP_APPROVED,
            CREDIT_APP_PENDING,
        ):
            raise CreditApplicationDenied(
                _("Credit Application was denied by Wells Fargo.")
            )

        # If the app status is approved, call signal handler
        if resp_data["application_status"] == CREDIT_APP_APPROVED:
            # Fire wfrs app approved signal
            wfrs_app_approved.send(sender=credit_app.__class__, app=credit_app)

        # Save the suffix of the account number
        credit_app.account_number = resp_data["credit_card_number"]
        credit_app.save()

        # Record an account inquiry
        main_applicant_full_name = "{}, {}".format(
            credit_app.main_applicant.last_name, credit_app.main_applicant.first_name
        )
        joint_applicant_full_name = None
        if credit_app.joint_applicant:
            joint_applicant_full_name = "{}, {}".format(
                credit_app.joint_applicant.last_name,
                credit_app.joint_applicant.first_name,
            )
        result = AccountInquiryResult.objects.create(
            credit_app_source=credit_app,
            prequal_response_source=None,
            account_number=resp_data["credit_card_number"],
            main_applicant_full_name=main_applicant_full_name,
            joint_applicant_full_name=joint_applicant_full_name,
            main_applicant_address=credit_app.main_applicant.address,
            joint_applicant_address=credit_app.joint_applicant.address
            if credit_app.joint_applicant
            else None,
            credit_limit=as_decimal(resp_data["credit_line"]),
            available_credit=as_decimal(resp_data["credit_line"]),
        )

        # Check if application approval is pending
        if resp_data["application_status"] == CREDIT_APP_PENDING:
            pending = CreditApplicationPending(
                _("Credit Application is approval is pending.")
            )
            pending.inquiry = result
            raise pending

        return result
