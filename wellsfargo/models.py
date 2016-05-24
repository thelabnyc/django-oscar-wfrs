from django.core.validators import MinValueValidator, MinLengthValidator, MaxValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_model
from .core.constants import LOCALE_CHOICES, TRANS_TYPES, TRANS_STATUSES

Account = get_model('oscar_accounts', 'Account')
Transfer = get_model('oscar_accounts', 'Transfer')


class AccountMetadata(models.Model):
    account = models.OneToOneField(Account,
        verbose_name=_("Account"),
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='wfrs_metadata')
    locale = models.CharField(_('Locale'), choices=LOCALE_CHOICES, max_length=5)
    account_number = models.CharField(_("Wells Fargo Account Number"), max_length=16, validators=[
        MinLengthValidator(16),
        MinLengthValidator(16),
    ])


class TransferMetadata(models.Model):
    transfer = models.OneToOneField(Transfer,
        verbose_name=_("Transfer"),
        on_delete=models.CASCADE,
        related_name='wfrs_metadata')
    type_code = models.CharField(_("Transaction Type"), choices=TRANS_TYPES, max_length=2)

    ticket_number = models.CharField(_("Ticket Number"), null=True, blank=True, max_length=12)
    plan_number = models.CharField(_("Plan Number"), max_length=4, validators=[
        MinLengthValidator(4),
        MinValueValidator(1001),
        MaxValueValidator(9999),
    ])

    auth_number = models.CharField(_("Authorization Number"), null=True, blank=True, max_length=6, default='000000')
    status = models.CharField(_("Status"), choices=TRANS_STATUSES, max_length=2)
    message = models.TextField(_("Message"))
    disclosure = models.TextField(_("Disclosure"))

    @classmethod
    def build_auth_request(cls, plan_number, ticket_number, amount):
        request = cls()
        request.plan_number = plan_number
        request.ticket_number = ticket_number
        request.amount = amount
        return request

    @property
    def type_name(self):
        return dict(TRANS_TYPES).get(self.type_code)

    @property
    def status_name(self):
        return dict(TRANS_STATUSES).get(self.status)
