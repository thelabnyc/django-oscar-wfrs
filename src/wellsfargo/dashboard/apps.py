from django.conf.urls import url
from oscar.core.application import OscarDashboardConfig


class WFRSDashboardConfig(OscarDashboardConfig):
    name = 'wellsfargo.dashboard'
    label = 'wellsfargo_dashboard'
    namespace = 'wellsfargo_dashboard'

    default_permissions = ['is_staff', ]

    def get_urls(self):
        from .views import (
            FinancingPlanListView,
            FinancingPlanCreateView,
            FinancingPlanUpdateView,
            FinancingPlanDeleteView,
            FinancingPlanBenefitListView,
            FinancingPlanBenefitCreateView,
            FinancingPlanBenefitUpdateView,
            FinancingPlanBenefitDeleteView,
            CreditApplicationListView,
            CreditApplicationDetailView,
            TransferMetadataListView,
            TransferMetadataDetailView,
            PreQualificationListView,
            PreQualificationDetailView,
            SDKApplicationListView,
        )
        urlpatterns = [
            url(r'^plans/$',
                FinancingPlanListView.as_view(),
                name='wfrs-plan-list'),
            url(r'^plans/new/$',
                FinancingPlanCreateView.as_view(),
                name='wfrs-plan-create'),
            url(r'^plans/(?P<pk>[0-9]+)/edit/$',
                FinancingPlanUpdateView.as_view(),
                name='wfrs-plan-edit'),
            url(r'^plans/(?P<pk>[0-9]+)/delete/$',
                FinancingPlanDeleteView.as_view(),
                name='wfrs-plan-delete'),

            url(r'^benefits/$',
                FinancingPlanBenefitListView.as_view(),
                name='wfrs-benefit-list'),
            url(r'^benefits/new/$',
                FinancingPlanBenefitCreateView.as_view(),
                name='wfrs-benefit-create'),
            url(r'^benefits/(?P<pk>[0-9]+)/edit/$',
                FinancingPlanBenefitUpdateView.as_view(),
                name='wfrs-benefit-edit'),
            url(r'^benefits/(?P<pk>[0-9]+)/delete/$',
                FinancingPlanBenefitDeleteView.as_view(),
                name='wfrs-benefit-delete'),

            url(r'^applications/$',
                CreditApplicationListView.as_view(),
                name='wfrs-application-list'),
            url(r'^applications/(?P<pk>[0-9]+)/$',
                CreditApplicationDetailView.as_view(),
                name='wfrs-application-detail'),

            url(r'^transfers/$',
                TransferMetadataListView.as_view(),
                name='wfrs-transfer-list'),
            url(r'^transfers/(?P<merchant_reference>[A-Za-z0-9\-]+)/$',
                TransferMetadataDetailView.as_view(),
                name='wfrs-transfer-detail'),

            url(r'^prequal-requests/$',
                PreQualificationListView.as_view(),
                name='wfrs-prequal-list'),
            url(r'^prequal-requests/(?P<uuid>[A-Za-z0-9\-]+)/$',
                PreQualificationDetailView.as_view(),
                name='wfrs-prequal-detail'),

            url(r'^sdk-applications/$',
                SDKApplicationListView.as_view(),
                name='wfrs-sdk-application-list'),
        ]
        return self.post_process_urls(urlpatterns)
