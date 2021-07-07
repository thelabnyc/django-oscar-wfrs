from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from oscar.core.loading import get_model
from oscar.models.fields import NullCharField
from ..core.constants import (
    TRANS_TYPE_AUTH,
    TRANS_TYPES,
    TRANS_STATUSES,
)
from .mixins import AccountNumberMixin


class TransferMetadata(AccountNumberMixin, models.Model):
    """
    Store WFRS specific metadata about a transfer
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Requesting User"),
        related_name="wfrs_transfers",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    merchant_name = NullCharField(_("Merchant Name"), max_length=200)
    merchant_num = NullCharField(_("Merchant Number"), max_length=200)
    merchant_reference = models.CharField(max_length=128, null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    type_code = models.CharField(
        _("Transaction Type"), choices=TRANS_TYPES, max_length=2
    )
    ticket_number = models.CharField(
        _("Ticket Number"), null=True, blank=True, max_length=12
    )
    financing_plan = models.ForeignKey(
        "wellsfargo.FinancingPlan",
        verbose_name=_("Plan Number"),
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )
    auth_number = models.CharField(
        _("Authorization Number"), null=True, blank=True, max_length=6, default="000000"
    )
    status = models.CharField(_("Status"), choices=TRANS_STATUSES, max_length=2)
    message = models.TextField(_("Message"))
    disclosure = models.TextField(_("Disclosure"))
    created_datetime = models.DateTimeField(_("Created"), auto_now_add=True)
    modified_datetime = models.DateTimeField(_("Modified"), auto_now=True)

    @classmethod
    def get_by_oscar_transaction(cls, transaction, type_code=TRANS_TYPE_AUTH):
        return (
            cls.objects.filter(merchant_reference=transaction.reference)
            .filter(type_code=type_code)
            .order_by("-created_datetime")
            .first()
        )

    @property
    def type_name(self):
        return dict(TRANS_TYPES).get(self.type_code)

    @property
    def status_name(self):
        return dict(TRANS_STATUSES).get(self.status)

    @property
    def financing_plan_number(self):
        return self.financing_plan.plan_number if self.financing_plan else None

    @cached_property
    def order(self):
        return self.get_order()

    def get_oscar_transaction(self):
        Transaction = get_model("payment", "Transaction")
        try:
            return Transaction.objects.get(reference=self.merchant_reference)
        except Transaction.DoesNotExist:
            return None

    def get_order(self):
        transaction = self.get_oscar_transaction()
        if not transaction:
            return None
        return transaction.source.order
