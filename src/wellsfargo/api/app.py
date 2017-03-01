from django.conf.urls import url
from oscar.core.application import Application

from .views import (
    SelectCreditAppView,
    USCreditAppView,
    USJointCreditAppView,
    CACreditAppView,
    CAJointCreditAppView,
    FinancingPlanView,
)


class WFRSAPIApplication(Application):
    def get_urls(self):
        urlpatterns = [
            url(r'^apply/$', SelectCreditAppView.as_view(), name='wfrs-api-apply-select'),

            url(r'^apply/us-individual/$', USCreditAppView.as_view(), name='wfrs-api-apply-us-individual'),
            url(r'^apply/us-joint/$', USJointCreditAppView.as_view(), name='wfrs-api-apply-us-join'),
            url(r'^apply/ca-individual/$', CACreditAppView.as_view(), name='wfrs-api-apply-ca-individual'),
            url(r'^apply/ca-joint/$', CAJointCreditAppView.as_view(), name='wfrs-api-apply-ca-joint'),

            url(r'^plans/$', FinancingPlanView.as_view(), name='wfrs-api-plan-list'),
        ]
        return self.post_process_urls(urlpatterns)


application = WFRSAPIApplication()
