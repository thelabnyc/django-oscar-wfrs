from django.urls import re_path
from oscar.core.application import OscarConfig


class WFRSAPIConfig(OscarConfig):
    name = "wellsfargo.api"
    label = "wellsfargo_api"
    namespace = "wellsfargo_api"

    def get_urls(self):
        from .views import (
            CreditApplicationView,
            FinancingPlanView,
            EstimatedPaymentView,
            UpdateAccountInquiryView,
            SubmitAccountInquiryView,
            PreQualificationSDKMerchantNumView,
            PreQualificationResumeView,
            PreQualificationRequestView,
            PreQualificationSDKResponseView,
            PreQualificationCustomerResponseView,
            PreQualificationSDKApplicationResultView,
        )

        urlpatterns = [
            re_path(
                r"^apply/$", CreditApplicationView.as_view(), name="wfrs-api-apply"
            ),
            re_path(
                r"^apply/update-inquiry/$",
                UpdateAccountInquiryView.as_view(),
                name="wfrs-api-update-inquiry",
            ),
            re_path(
                r"^plans/$", FinancingPlanView.as_view(), name="wfrs-api-plan-list"
            ),
            re_path(
                r"^estimated-payment/$",
                EstimatedPaymentView.as_view(),
                name="wfrs-api-estimated-payment",
            ),
            re_path(
                r"^inquiry/$",
                SubmitAccountInquiryView.as_view(),
                name="wfrs-api-acct-inquiry",
            ),
            re_path(
                r"^prequal/$",
                PreQualificationRequestView.as_view(),
                name="wfrs-api-prequal",
            ),
            re_path(
                r"^prequal/resume/(?P<signed_prequal_request_id>[A-z0-9-_=:]+)/$",
                PreQualificationResumeView.as_view(),
                name="wfrs-api-prequal-resume",
            ),
            re_path(
                r"^prequal/sdk-merchant-num/$",
                PreQualificationSDKMerchantNumView.as_view(),
                name="wfrs-api-prequal-sdk-merchant-num",
            ),
            re_path(
                r"^prequal/sdk-response/$",
                PreQualificationSDKResponseView.as_view(),
                name="wfrs-api-prequal-sdk-response",
            ),
            re_path(
                r"^prequal/sdk-application-result/$",
                PreQualificationSDKApplicationResultView.as_view(),
                name="wfrs-api-prequal-sdk-app-result",
            ),
            re_path(
                r"^prequal/set-customer-response/$",
                PreQualificationCustomerResponseView.as_view(),
                name="wfrs-api-prequal-customer-response",
            ),
        ]
        return self.post_process_urls(urlpatterns)
