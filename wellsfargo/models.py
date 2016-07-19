from decimal import Decimal
from django.core.validators import MinValueValidator, MinLengthValidator, MaxValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_model, get_class
from .core.constants import LOCALE_CHOICES, TRANS_TYPES, TRANS_STATUSES

Account = get_model('oscar_accounts', 'Account')
Transfer = get_model('oscar_accounts', 'Transfer')
Benefit = get_model('offer', 'Benefit')

PostOrderAction = get_class('offer.results', 'PostOrderAction')


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
    plan_number = models.PositiveIntegerField(_("Plan Number"), validators=[
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


class FinancingPlan(models.Model):
    plan_number = models.PositiveIntegerField(_("Plan Number"), unique=True, validators=[
        MinValueValidator(1001),
        MaxValueValidator(9999),
    ])
    description = models.TextField(_("Description"))
    apr = models.DecimalField(_("Annual percentage rate (0.0 – 100.0)"), max_digits=5, decimal_places=2, default='0.00', validators=[
        MinValueValidator(Decimal('0.00')),
        MaxValueValidator(Decimal('100.00')),
    ])
    term_months = models.PositiveSmallIntegerField(_("Term Length (months)"), default=12)

    class Meta:
        ordering = ('plan_number', )

    def __str__(self):
        return "%s (plan number %s)" % (self.description, self.plan_number)


class FinancingPlanBenefit(Benefit):
    group_name = models.CharField(_('Name'), max_length=200)
    plans = models.ManyToManyField(FinancingPlan)

    class Meta(Benefit.Meta):
        app_label = 'wellsfargo'

    def __str__(self):
        return self.group_name

    def apply(self, basket, condition, offer):
        return PostOrderAction("Financing is available for your order")

    def apply_deferred(self, basket, order, application):
        return "Something happened"

    @property
    def name(self):
        return self.group_name

    @property
    def description(self):
        nums = ', '.join([str(p.plan_number) for p in self.plans.all()])
        return "Causes the following Wells Fargo financing plans to be available: %s" % nums

    def save(self, *args, **kwargs):
        self.proxy_class = '%s.%s' % (FinancingPlanBenefit.__module__, FinancingPlanBenefit.__name__)
        return super().save(*args, **kwargs)
