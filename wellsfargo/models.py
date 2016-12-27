from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core import exceptions
from django.core.validators import MinValueValidator, MinLengthValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_model, get_class
from oscar_accounts.core import redemptions_account
from .core.constants import LOCALE_CHOICES, TRANS_TYPES, TRANS_STATUSES, TRANS_TYPE_AUTH
from .core.applications import (
    USCreditAppMixin,
    BaseCreditAppMixin,
    USJointCreditAppMixin,
    BaseJointCreditAppMixin,
    CACreditAppMixin,
    CAJointCreditAppMixin
)

Account = get_model('oscar_accounts', 'Account')
Transfer = get_model('oscar_accounts', 'Transfer')
Benefit = get_model('offer', 'Benefit')

PostOrderAction = get_class('offer.results', 'PostOrderAction')


class AccountOwner(User):
    """Only exists so that our haystack search index doesn't conflict with any other haystack indexes on auth.User"""
    class Meta:
        proxy = True


class APICredentials(models.Model):
    username = models.CharField(_('WFRS API Username'), max_length=200)
    password = models.CharField(_('WFRS API Password'), max_length=200)
    merchant_num = models.CharField(_('WFRS API Merchant Number'), max_length=200)
    user_group = models.ForeignKey(Group, null=True, blank=True)
    priority = models.IntegerField(_('Priority Order'), default=1)

    class Meta:
        ordering = ('-priority', '-id')
        verbose_name = _('API Credentials')
        verbose_name_plural = _('API Credentials')


    @classmethod
    def get_credentials(cls, user=None):
        if user and user.is_authenticated():
            creds = cls.objects.filter(user_group__in=user.groups.all()).first()
            if creds:
                return creds
        creds = cls.objects.filter(user_group=None).first()
        if creds:
            return creds
        return cls()


    def __str__(self):
        return "%s:xxxx@wfrs/%s" % (self.username, self.merchant_num)


class FinancingPlan(models.Model):
    """
    An individual WFRS plan number and related metadata about it
    """
    plan_number = models.PositiveIntegerField(_("Plan Number"), unique=True, validators=[
        MinValueValidator(1001),
        MaxValueValidator(9999),
    ])
    description = models.TextField(_("Description"), blank=True, default='')
    apr = models.DecimalField(_("Annual percentage rate (0.0 – 100.0)"), max_digits=5, decimal_places=2, default='0.00', validators=[
        MinValueValidator(Decimal('0.00')),
        MaxValueValidator(Decimal('100.00')),
    ])
    term_months = models.PositiveSmallIntegerField(_("Term Length (months)"), default=12)
    is_default_plan = models.BooleanField(_("Is Default Plan?"), default=False)

    class Meta:
        ordering = ('plan_number', )

    def __str__(self):
        return "%s (plan number %s)" % (self.description, self.plan_number)

    def save(self, *args, **kwargs):
        if self.is_default_plan:
            self.__class__._default_manager.filter(is_default_plan=True).update(is_default_plan=False)
        super().save(*args, **kwargs)


class FinancingPlanBenefit(Benefit):
    """
    A group of WFRS plan numbers made available to a customer as the applied benefit of an offer or voucher. This
    makes it possible to offer different plan numbers to different customers based on any of the normal offer conditions.
    """
    group_name = models.CharField(_('Name'), max_length=200)
    plans = models.ManyToManyField(FinancingPlan)

    class Meta(Benefit.Meta):
        app_label = 'wellsfargo'

    def __str__(self):
        return self.group_name

    def apply(self, basket, condition, offer):
        return PostOrderAction("Financing is available for your order")

    def apply_deferred(self, basket, order, application):
        return "Financing was available for your order: %s" % self.group_name

    @property
    def name(self):
        return self.group_name

    @property
    def description(self):
        nums = ', '.join([str(p.plan_number) for p in self.plans.all()])
        return "Causes the following Wells Fargo financing plans to be available: %s" % nums

    def _clean(self):
        group_name = getattr(self, 'group_name', None)
        if not group_name:
            raise exceptions.ValidationError(_((
                "Wells Fargo Financing Plan Benefit must have a group name. "
                "Use the Financing > Wells Fargo Plan Group dashboard to create this type of benefit."
            )))


class AccountMetadata(models.Model):
    """
    Store WFRS specific metadata about an account
    """
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
    billing_address = models.OneToOneField('order.BillingAddress',
        null=True, blank=True,
        verbose_name=_("Billing Address"),
        on_delete=models.SET_NULL,
        related_name='+')


class TransferMetadata(models.Model):
    """
    Store WFRS specific metadata about a transfer
    """
    transfer = models.OneToOneField(Transfer,
        verbose_name=_("Transfer"),
        on_delete=models.CASCADE,
        related_name='wfrs_metadata')
    type_code = models.CharField(_("Transaction Type"), choices=TRANS_TYPES, max_length=2)

    ticket_number = models.CharField(_("Ticket Number"), null=True, blank=True, max_length=12)
    financing_plan = models.ForeignKey(FinancingPlan,
        verbose_name=_("Plan Number"),
        null=True, blank=False,
        on_delete=models.SET_NULL)

    auth_number = models.CharField(_("Authorization Number"), null=True, blank=True, max_length=6, default='000000')
    status = models.CharField(_("Status"), choices=TRANS_STATUSES, max_length=2)
    message = models.TextField(_("Message"))
    disclosure = models.TextField(_("Disclosure"))

    @classmethod
    def build_auth_request(cls, financing_plan, ticket_number, amount):
        request = cls()
        request.financing_plan = financing_plan
        request.ticket_number = ticket_number
        request.amount = amount
        return request

    @property
    def type_name(self):
        return dict(TRANS_TYPES).get(self.type_code)

    @property
    def status_name(self):
        return dict(TRANS_STATUSES).get(self.status)


class TransactionRequest(models.Model):
    """
    A log of a request for a WFRS transaction
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        verbose_name=_("Requesting User"),
        related_name='transaction_requests',
        on_delete=models.CASCADE)
    type_code = models.CharField(_("Transaction Type"), choices=TRANS_TYPES, default=TRANS_TYPE_AUTH, max_length=2)
    source_account = models.ForeignKey(Account,
        verbose_name=_("Source Account"),
        related_name='source_requests',
        on_delete=models.CASCADE)
    dest_account = models.ForeignKey(Account,
        verbose_name=_("Destination Account"),
        related_name='dest_requests',
        on_delete=models.CASCADE)
    ticket_number = models.CharField(_("Ticket Number"), null=True, blank=True, max_length=12)
    financing_plan = models.ForeignKey(FinancingPlan,
        verbose_name=_("Plan Number"),
        null=True, blank=False,
        on_delete=models.SET_NULL)
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    auth_number = models.CharField(_("Authorization Number"), max_length=6, default='000000', validators=[
        MinLengthValidator(6),
        MinLengthValidator(6),
        RegexValidator(r'^[0-9]{6}$'),
    ])
    transfer = models.OneToOneField(Transfer,
        null=True, editable=False,
        verbose_name=_("Transfer"),
        on_delete=models.SET_NULL,
        related_name='transfer_request')
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    @classmethod
    def build_auth_request(cls, user, source_account, financing_plan, amount, dest_account=None, ticket_number=None):
        if not dest_account:
            dest_account = redemptions_account()
        request = cls()
        request.user = user
        request.type_code = TRANS_TYPE_AUTH
        request.source_account = source_account
        request.dest_account = dest_account
        request.ticket_number = ticket_number
        request.financing_plan = financing_plan
        request.amount = amount
        request.auth_number = '000000'
        request.save()
        return request


class USCreditApp(USCreditAppMixin, BaseCreditAppMixin):
    APP_TYPE_CODE = 'us-individual'
    account = models.OneToOneField(Account,
        null=True, editable=False,
        verbose_name=_("Account"),
        on_delete=models.SET_NULL,
        related_name='us_individual_credit_app')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=False, blank=False,
        verbose_name=_("Owner"),
        related_name='us_individual_credit_apps',
        on_delete=models.CASCADE)



class USJointCreditApp(USJointCreditAppMixin, BaseJointCreditAppMixin):
    APP_TYPE_CODE = 'us-joint'
    account = models.OneToOneField(Account,
        null=True, editable=False,
        verbose_name=_("Account"),
        on_delete=models.SET_NULL,
        related_name='us_joint_credit_app')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=False, blank=False,
        verbose_name=_("Owner"),
        related_name='us_joint_credit_apps',
        on_delete=models.CASCADE)


class CACreditApp(CACreditAppMixin, BaseCreditAppMixin):
    APP_TYPE_CODE = 'ca-individual'
    account = models.OneToOneField(Account,
        null=True, editable=False,
        verbose_name=_("Account"),
        on_delete=models.SET_NULL,
        related_name='ca_individual_credit_app')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=False, blank=False,
        verbose_name=_("Owner"),
        related_name='ca_individual_credit_apps',
        on_delete=models.CASCADE)


class CAJointCreditApp(CAJointCreditAppMixin, BaseJointCreditAppMixin):
    APP_TYPE_CODE = 'ca-joint'
    account = models.OneToOneField(Account,
        null=True, editable=False,
        verbose_name=_("Account"),
        on_delete=models.SET_NULL,
        related_name='ca_joint_credit_app')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=False, blank=False,
        verbose_name=_("Owner"),
        related_name='ca_joint_credit_apps',
        on_delete=models.CASCADE)
