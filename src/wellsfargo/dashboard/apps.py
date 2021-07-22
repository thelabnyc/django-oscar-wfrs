from django.urls import re_path
from oscar.core.application import OscarDashboardConfig


class WFRSDashboardConfig(OscarDashboardConfig):
    name = "wellsfargo.dashboard"
    label = "wellsfargo_dashboard"
    namespace = "wellsfargo_dashboard"

    default_permissions = [
        "is_staff",
    ]

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
            re_path(
                r"^plans/$", FinancingPlanListView.as_view(), name="wfrs-plan-list"
            ),
            re_path(
                r"^plans/new/$",
                FinancingPlanCreateView.as_view(),
                name="wfrs-plan-create",
            ),
            re_path(
                r"^plans/(?P<pk>[0-9]+)/edit/$",
                FinancingPlanUpdateView.as_view(),
                name="wfrs-plan-edit",
            ),
            re_path(
                r"^plans/(?P<pk>[0-9]+)/delete/$",
                FinancingPlanDeleteView.as_view(),
                name="wfrs-plan-delete",
            ),
            re_path(
                r"^benefits/$",
                FinancingPlanBenefitListView.as_view(),
                name="wfrs-benefit-list",
            ),
            re_path(
                r"^benefits/new/$",
                FinancingPlanBenefitCreateView.as_view(),
                name="wfrs-benefit-create",
            ),
            re_path(
                r"^benefits/(?P<pk>[0-9]+)/edit/$",
                FinancingPlanBenefitUpdateView.as_view(),
                name="wfrs-benefit-edit",
            ),
            re_path(
                r"^benefits/(?P<pk>[0-9]+)/delete/$",
                FinancingPlanBenefitDeleteView.as_view(),
                name="wfrs-benefit-delete",
            ),
            re_path(
                r"^applications/$",
                CreditApplicationListView.as_view(),
                name="wfrs-application-list",
            ),
            re_path(
                r"^applications/(?P<pk>[0-9]+)/$",
                CreditApplicationDetailView.as_view(),
                name="wfrs-application-detail",
            ),
            re_path(
                r"^transfers/$",
                TransferMetadataListView.as_view(),
                name="wfrs-transfer-list",
            ),
            re_path(
                r"^transfers/(?P<merchant_reference>[A-Za-z0-9\-]+)/$",
                TransferMetadataDetailView.as_view(),
                name="wfrs-transfer-detail",
            ),
            re_path(
                r"^prequal-requests/$",
                PreQualificationListView.as_view(),
                name="wfrs-prequal-list",
            ),
            re_path(
                r"^prequal-requests/(?P<uuid>[A-Za-z0-9\-]+)/$",
                PreQualificationDetailView.as_view(),
                name="wfrs-prequal-detail",
            ),
            re_path(
                r"^sdk-applications/$",
                SDKApplicationListView.as_view(),
                name="wfrs-sdk-application-list",
            ),
        ]
        return self.post_process_urls(urlpatterns)
