from django.conf.urls import url
from oscar.core.application import Application

from .views import (
    SubmitTransactionView,
    ApplicationSelectionView,
    CreditApplicationView
)


class WFRSDashboardApplication(Application):
    name = None
    default_permissions = ['is_staff', ]

    apply_step1 = ApplicationSelectionView
    apply_step2 = CreditApplicationView
    submit_transaction = SubmitTransactionView

    def get_urls(self):
        urlpatterns = [
            url(r'^apply/$',
                self.apply_step1.as_view(),
                name='wfrs-apply-step1'),
            url(r'^apply/(?P<region>\w+)/(?P<language>\w+)/(?P<app_type>\w+)/$',
                self.apply_step2.as_view(),
                name='wfrs-apply-step2'),
            url(r'^transaction/new/(?P<source_id>\d+)/$',
                self.submit_transaction.as_view(),
                name='wfrs-submit-transaction'),
        ]
        return self.post_process_urls(urlpatterns)


application = WFRSDashboardApplication()
