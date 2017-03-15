from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import Group
from django.core import exceptions
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_model, get_class
from .core.constants import TRANS_TYPES, TRANS_STATUSES
from .core.applications import (
    USCreditAppMixin,
    BaseCreditAppMixin,
    USJointCreditAppMixin,
    BaseJointCreditAppMixin,
    CACreditAppMixin,
    CAJointCreditAppMixin
)
from .security import encrypt_account_number, decrypt_account_number
import logging

Benefit = get_model('offer', 'Benefit')
Transaction = get_model('payment', 'Transaction')
PostOrderAction = get_class('offer.results', 'PostOrderAction')

logger = logging.getLogger(__name__)


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
        logger.error('Application requested WFRS API Credentials for use by user {}, but none exist in the database for them.'.format(user))
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
    allow_credit_application = models.BooleanField(_('Allow new credit applications when user is eligible for this plan?'), default=True)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy_class = '%s.%s' % (self.__class__.__module__, self.__class__.__name__)

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


class TransferMetadata(models.Model):
    """
    Store WFRS specific metadata about a transfer
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        verbose_name=_("Requesting User"),
        related_name='wfrs_transfers',
        null=True, blank=True,
        on_delete=models.CASCADE)
    credentials = models.ForeignKey(APICredentials,
        verbose_name=_("API Credentials"),
        related_name='transfers',
        null=True, blank=True,
        on_delete=models.SET_NULL)
    last4_account_number = models.CharField(_("Last 4 digits of account number"), max_length=4)
    encrypted_account_number = models.BinaryField(null=True)
    merchant_reference = models.CharField(max_length=128, null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=12)
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
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    @classmethod
    def get_by_oscar_transaction(cls, transaction):
        try:
            return cls.objects.get(merchant_reference=transaction.reference)
        except TransferMetadata.DoesNotExist:
            return None

    @property
    def type_name(self):
        return dict(TRANS_TYPES).get(self.type_code)

    @property
    def status_name(self):
        return dict(TRANS_STATUSES).get(self.status)

    @property
    def masked_account_number(self):
        return 'xxxxxxxxxxxx{}'.format(self.last4_account_number or 'xxxx')

    @property
    def account_number(self):
        acct_num = None
        if self.encrypted_account_number:
            acct_num = decrypt_account_number(self.encrypted_account_number)
        if not acct_num:
            acct_num = self.masked_account_number
        return acct_num

    @account_number.setter
    def account_number(self, value):
        if len(value) != 16:
            raise ValueError('Account number must be 16 digits long')
        self.last4_account_number = value[-4:]
        self.encrypted_account_number = encrypt_account_number(value)

    def get_oscar_transaction(self):
        try:
            return Transaction.objects.get(reference=self.merchant_reference)
        except Transaction.DoesNotExist:
            return None

    def get_order(self):
        transaction = self.get_oscar_transaction()
        if not transaction:
            return None
        return transaction.source.order

    def purge_encrypted_account_number(self):
        self.encrypted_account_number = None
        self.save()


class USCreditApp(USCreditAppMixin, BaseCreditAppMixin):
    APP_TYPE_CODE = 'us-individual'
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Owner"),
        help_text=_("Select the user user who is applying and who will own (be the primary user of) this account."),
        related_name='us_individual_credit_apps',
        on_delete=models.CASCADE)
    submitting_user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Submitting User"),
        help_text=_("Select the user who filled out and submitted the credit application (not always the same as the user who is applying for credit)."),
        related_name='+',
        on_delete=models.SET_NULL)



class USJointCreditApp(USJointCreditAppMixin, BaseJointCreditAppMixin):
    APP_TYPE_CODE = 'us-joint'
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Owner"),
        help_text=_("Select the user user who is applying and who will own (be the primary user of) this account."),
        related_name='us_joint_credit_apps',
        on_delete=models.CASCADE)
    submitting_user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Submitting User"),
        help_text=_("Select the user who filled out and submitted the credit application (not always the same as the user who is applying for credit)."),
        related_name='+',
        on_delete=models.SET_NULL)


class CACreditApp(CACreditAppMixin, BaseCreditAppMixin):
    APP_TYPE_CODE = 'ca-individual'
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Owner"),
        help_text=_("Select the user user who is applying and who will own (be the primary user of) this account."),
        related_name='ca_individual_credit_apps',
        on_delete=models.CASCADE)
    submitting_user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Submitting User"),
        help_text=_("Select the user who filled out and submitted the credit application (not always the same as the user who is applying for credit)."),
        related_name='+',
        on_delete=models.SET_NULL)


class CAJointCreditApp(CAJointCreditAppMixin, BaseJointCreditAppMixin):
    APP_TYPE_CODE = 'ca-joint'
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Owner"),
        help_text=_("Select the user user who is applying and who will own (be the primary user of) this account."),
        related_name='ca_joint_credit_apps',
        on_delete=models.CASCADE)
    submitting_user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Submitting User"),
        help_text=_("Select the user who filled out and submitted the credit application (not always the same as the user who is applying for credit)."),
        related_name='+',
        on_delete=models.SET_NULL)
