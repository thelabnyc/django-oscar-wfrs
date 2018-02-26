from django.conf.urls import url
from oscar.core.application import Application

from .views import (
    ApplicationSelectionView,
    CreditApplicationView,
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
)


class WFRSDashboardApplication(Application):
    name = None
    default_permissions = ['is_staff', ]

    apply_step1 = ApplicationSelectionView
    apply_step2 = CreditApplicationView
    plan_list = FinancingPlanListView
    plan_create = FinancingPlanCreateView
    plan_update = FinancingPlanUpdateView
    plan_delete = FinancingPlanDeleteView
    benefit_list = FinancingPlanBenefitListView
    benefit_create = FinancingPlanBenefitCreateView
    benefit_update = FinancingPlanBenefitUpdateView
    benefit_delete = FinancingPlanBenefitDeleteView
    application_list = CreditApplicationListView
    application_detail = CreditApplicationDetailView
    transfer_list = TransferMetadataListView
    transfer_detail = TransferMetadataDetailView
    prequal_list = PreQualificationListView
    prequal_detail = PreQualificationDetailView

    def get_urls(self):
        urlpatterns = [
            url(r'^apply/$',
                self.apply_step1.as_view(),
                name='wfrs-apply-step1'),
            url(r'^apply/(?P<region>\w+)/(?P<language>\w+)/(?P<app_type>\w+)/$',
                self.apply_step2.as_view(),
                name='wfrs-apply-step2'),

            url(r'^plans/$',
                self.plan_list.as_view(),
                name='wfrs-plan-list'),
            url(r'^plans/new/$',
                self.plan_create.as_view(),
                name='wfrs-plan-create'),
            url(r'^plans/(?P<pk>[0-9]+)/edit/$',
                self.plan_update.as_view(),
                name='wfrs-plan-edit'),
            url(r'^plans/(?P<pk>[0-9]+)/delete/$',
                self.plan_delete.as_view(),
                name='wfrs-plan-delete'),

            url(r'^benefits/$',
                self.benefit_list.as_view(),
                name='wfrs-benefit-list'),
            url(r'^benefits/new/$',
                self.benefit_create.as_view(),
                name='wfrs-benefit-create'),
            url(r'^benefits/(?P<pk>[0-9]+)/edit/$',
                self.benefit_update.as_view(),
                name='wfrs-benefit-edit'),
            url(r'^benefits/(?P<pk>[0-9]+)/delete/$',
                self.benefit_delete.as_view(),
                name='wfrs-benefit-delete'),

            url(r'^applications/$',
                self.application_list.as_view(),
                name='wfrs-application-list'),
            url(r'^applications/(?P<app_type>[a-z\-]+)/(?P<pk>[0-9]+)/$',
                self.application_detail.as_view(),
                name='wfrs-application-detail'),


            url(r'^transfers/$',
                self.transfer_list.as_view(),
                name='wfrs-transfer-list'),
            url(r'^transfers/(?P<merchant_reference>[A-Za-z0-9\-]+)/$',
                self.transfer_detail.as_view(),
                name='wfrs-transfer-detail'),

            url(r'^prequal-requests/$',
                self.prequal_list.as_view(),
                name='wfrs-prequal-list'),
            url(r'^prequal-requests/(?P<uuid>[A-Za-z0-9\-]+)/$',
                self.prequal_detail.as_view(),
                name='wfrs-prequal-detail'),
        ]
        return self.post_process_urls(urlpatterns)


application = WFRSDashboardApplication()
