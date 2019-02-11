from django.conf.urls import url
from oscar.core.application import Application

from .views import (
    SelectCreditAppView,
    USCreditAppView,
    USJointCreditAppView,
    CACreditAppView,
    CAJointCreditAppView,
    FinancingPlanView,
    EstimatedPaymentView,
    UpdateAccountInquiryView,
    SubmitAccountInquiryView,
    PreQualificationRequestView,
    PreQualificationSDKResponseView,
    PreQualificationCustomerResponseView,
    PreQualificationCustomerRedirectView,
    PreQualificationSDKApplicationResultView,
)


class WFRSAPIApplication(Application):
    def get_urls(self):
        urlpatterns = [
            url(r'^apply/$', SelectCreditAppView.as_view(), name='wfrs-api-apply-select'),

            url(r'^apply/us-individual/$', USCreditAppView.as_view(), name='wfrs-api-apply-us-individual'),
            url(r'^apply/us-joint/$', USJointCreditAppView.as_view(), name='wfrs-api-apply-us-join'),
            url(r'^apply/ca-individual/$', CACreditAppView.as_view(), name='wfrs-api-apply-ca-individual'),
            url(r'^apply/ca-joint/$', CAJointCreditAppView.as_view(), name='wfrs-api-apply-ca-joint'),

            url(r'^apply/update-inquiry/$', UpdateAccountInquiryView.as_view(), name='wfrs-api-update-inquiry'),

            url(r'^plans/$', FinancingPlanView.as_view(), name='wfrs-api-plan-list'),

            url(r'^estimated-payment/$', EstimatedPaymentView.as_view(), name='wfrs-api-estimated-payment'),

            url(r'^inquiry/$', SubmitAccountInquiryView.as_view(), name='wfrs-api-acct-inquiry'),

            url(r'^prequal/$', PreQualificationRequestView.as_view(), name='wfrs-api-prequal'),
            url(r'^prequal/sdk-response/$', PreQualificationSDKResponseView.as_view(), name='wfrs-api-prequal-sdk-response'),
            url(r'^prequal/sdk-application-result/$', PreQualificationSDKApplicationResultView.as_view(), name='wfrs-api-prequal-sdk-app-result'),
            url(r'^prequal/set-customer-response/$', PreQualificationCustomerResponseView.as_view(),
                name='wfrs-api-prequal-customer-response'),
            url(r'^prequal/application-complete/$', PreQualificationCustomerRedirectView.as_view(),
                name='wfrs-api-prequal-app-complete'),
        ]
        return self.post_process_urls(urlpatterns)


application = WFRSAPIApplication()
