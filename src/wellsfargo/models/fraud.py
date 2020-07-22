from django.db import models
from django.utils.translation import gettext_lazy as _



class FraudScreenResult(models.Model):
    DECISION_REJECT = 'REJECT'
    DECISION_ACCEPT = 'ACCEPT'
    DECISION_ERROR = 'ERROR'
    DECISION_REVIEW = 'REVIEW'

    screen_type = models.CharField(_("Fraud Screen Type"), max_length=25)
    order = models.ForeignKey('order.Order',
        verbose_name=_("Order"),
        related_name='wfrs_fraud_screen_results',
        on_delete=models.CASCADE)
    reference = models.CharField(_("Reference"), max_length=128)
    decision = models.CharField(_("Decision"), max_length=25, choices=(
        (DECISION_REJECT, _("Transaction was rejected")),
        (DECISION_ACCEPT, _("Transaction was accepted")),
        (DECISION_ERROR, _("Error occurred while running fraud screen")),
        (DECISION_REVIEW, _("Transaction was flagged for manual review")),
    ))
    message = models.TextField(_("Message"))
    created_datetime = models.DateTimeField(_("Created On"), auto_now_add=True)
    modified_datetime = models.DateTimeField(_("Modified On"), auto_now=True)

    class Meta:
        ordering = ('-created_datetime', '-id')
        verbose_name = _('Fraud Screen Result')
        verbose_name_plural = _('Fraud Screen Results')

    def __str__(self):
        return self.message
