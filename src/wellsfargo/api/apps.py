from django.conf.urls import url
from oscar.core.application import OscarConfig


class WFRSAPIConfig(OscarConfig):
    name = 'wellsfargo.api'
    label = 'wellsfargo_api'
    namespace = 'wellsfargo_api'

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
            url(r'^apply/$', CreditApplicationView.as_view(), name='wfrs-api-apply'),

            url(r'^apply/update-inquiry/$', UpdateAccountInquiryView.as_view(), name='wfrs-api-update-inquiry'),

            url(r'^plans/$', FinancingPlanView.as_view(), name='wfrs-api-plan-list'),

            url(r'^estimated-payment/$', EstimatedPaymentView.as_view(), name='wfrs-api-estimated-payment'),

            url(r'^inquiry/$', SubmitAccountInquiryView.as_view(), name='wfrs-api-acct-inquiry'),

            url(r'^prequal/$', PreQualificationRequestView.as_view(),
                name='wfrs-api-prequal'),

            url(r'^prequal/resume/(?P<signed_prequal_request_id>[A-z0-9-_=:]+)/$', PreQualificationResumeView.as_view(),
                name='wfrs-api-prequal-resume'),

            url(r'^prequal/sdk-merchant-num/$', PreQualificationSDKMerchantNumView.as_view(),
                name='wfrs-api-prequal-sdk-merchant-num'),

            url(r'^prequal/sdk-response/$', PreQualificationSDKResponseView.as_view(),
                name='wfrs-api-prequal-sdk-response'),

            url(r'^prequal/sdk-application-result/$', PreQualificationSDKApplicationResultView.as_view(),
                name='wfrs-api-prequal-sdk-app-result'),

            url(r'^prequal/set-customer-response/$', PreQualificationCustomerResponseView.as_view(),
                name='wfrs-api-prequal-customer-response'),

        ]
        return self.post_process_urls(urlpatterns)
