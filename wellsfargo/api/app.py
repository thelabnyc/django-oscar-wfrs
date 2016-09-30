from django.conf.urls import url
from oscar.core.application import Application

from .views import (
    AutocompleteAccountOwnerView,
    SelectCreditAppView,
    USCreditAppView,
    USJointCreditAppView,
    CACreditAppView,
    CAJointCreditAppView,
    AccountView,
    FinancingPlanView,
)


class WFRSAPIApplication(Application):
    def get_urls(self):
        urlpatterns = [
            url(r'^user-autocomplete/$', AutocompleteAccountOwnerView.as_view(), name='wfrs-api-user-autocomplete'),

            url(r'^apply/$', SelectCreditAppView.as_view(), name='wfrs-api-apply-select'),

            url(r'^apply/us-individual/$', USCreditAppView.as_view(), name='wfrs-api-apply-us-individual'),
            url(r'^apply/us-joint/$', USJointCreditAppView.as_view(), name='wfrs-api-apply-us-join'),
            url(r'^apply/ca-individual/$', CACreditAppView.as_view(), name='wfrs-api-apply-ca-individual'),
            url(r'^apply/ca-joint/$', CAJointCreditAppView.as_view(), name='wfrs-api-apply-ca-joint'),

            url(r'^accounts/$', AccountView.as_view({'get': 'list'}), name='wfrs-api-account-list'),
            url(r'^accounts/(?P<pk>[0-9]+)/$', AccountView.as_view({'get': 'retrieve'}), name='wfrs-api-account-detail'),

            url(r'^plans/$', FinancingPlanView.as_view(), name='wfrs-api-plan-list'),
        ]
        return self.post_process_urls(urlpatterns)


application = WFRSAPIApplication()
