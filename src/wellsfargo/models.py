from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import Group
from django.core import exceptions
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_model, get_class
from oscar.models.fields import PhoneNumberField
from .core.constants import (
    TRANS_TYPE_AUTH,
    TRANS_TYPES,
    TRANS_STATUSES,
    INQUIRY_STATUSES,
    EN_US,
    PREQUAL_LOCALE_CHOICES,
    ENTRY_POINT_WEB,
    ENTRY_POINT_CHOICES,
    PREQUAL_TRANS_STATUS_APPROVED,
    PREQUAL_TRANS_STATUS_CHOICES,
    PREQUAL_CUSTOMER_RESP_NONE,
    PREQUAL_CUSTOMER_RESP_CHOICES,
)
from .core.applications import (
    USCreditAppMixin,
    BaseCreditAppMixin,
    USJointCreditAppMixin,
    BaseJointCreditAppMixin,
    CACreditAppMixin,
    CAJointCreditAppMixin,
)
from .core.fields import USStateField, USZipCodeField
from .security import encrypt_account_number, decrypt_account_number
import logging
import uuid

Benefit = get_model('offer', 'Benefit')
PostOrderAction = get_class('offer.results', 'PostOrderAction')

logger = logging.getLogger(__name__)


def _max_len(choices):
    """Given a list of char field choices, return the field max length"""
    lengths = [len(choice) for choice, _ in choices]
    return max(lengths)



class APICredentials(models.Model):
    name = models.CharField(_('Merchant Name'), max_length=200, default='Default')
    username = models.CharField(_('WFRS API Username'), max_length=200)
    password = models.CharField(_('WFRS API Password'), max_length=200)
    merchant_num = models.CharField(_('WFRS API Merchant Number'), max_length=200)
    user_group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.CASCADE)
    priority = models.IntegerField(_('Priority Order'), default=1)

    class Meta:
        ordering = ('-priority', '-id')
        verbose_name = _('API Credentials')
        verbose_name_plural = _('API Credentials')


    @classmethod
    def get_credentials(cls, user=None):
        if user and user.is_authenticated:
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
    fine_print_superscript = models.CharField(_("Fine Print Superscript"), blank=True, default='', max_length=10)
    apr = models.DecimalField(_("Annual percentage rate (0.0 – 100.0)"), max_digits=5, decimal_places=2, default='0.00', validators=[
        MinValueValidator(Decimal('0.00')),
        MaxValueValidator(Decimal('100.00')),
    ])
    term_months = models.PositiveSmallIntegerField(_("Term Length (months)"), default=12)
    product_price_threshold = models.DecimalField(_("Minimum Product Price for Plan Availability Advertising"),
        decimal_places=2,
        max_digits=12,
        default='0.00',
        validators=[MinValueValidator(Decimal('0.00'))])
    advertising_enabled = models.BooleanField(_("Is Advertising Enabled for Plan?"), default=False)
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
        condition.consume_items(offer, basket, [])
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



class FraudScreenResult(models.Model):
    DECISION_REJECT = 'REJECT'
    DECISION_ACCEPT = 'ACCEPT'
    DECISION_ERROR = 'ERROR'
    DECISION_REVIEW = 'REVIEW'

    screen_type = models.CharField(_("Fraud Screen Type"), max_length=25)
    order = models.ForeignKey('order.Order', related_name='wfrs_fraud_screen_results', on_delete=models.CASCADE)
    reference = models.CharField(_("Reference"), max_length=128)
    decision = models.CharField(_("Decision"), max_length=25, choices=(
        (DECISION_REJECT, _("Transaction was rejected")),
        (DECISION_ACCEPT, _("Transaction was accepted")),
        (DECISION_ERROR, _("Error occurred while running fraud screen")),
        (DECISION_REVIEW, _("Transaction was flagged for manual review")),
    ))
    message = models.TextField(_("Message"))
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_datetime', '-id')


    def __str__(self):
        return self.message



class AccountInquiryResult(models.Model):
    prequal_response_source = models.ForeignKey('wellsfargo.PreQualificationResponse',
        verbose_name=_("Pre-Qualification Source"),
        related_name='account_inquiries',
        null=True, blank=True,
        on_delete=models.SET_NULL)

    status = models.CharField(_("Status"), choices=INQUIRY_STATUSES, max_length=2)

    last4_account_number = models.CharField(_("Last 4 digits of account number"), max_length=4)
    _full_account_number = None

    first_name = models.CharField(_("First Name"), max_length=50)
    middle_initial = models.CharField(_("Middle Initial"), null=True, blank=True, max_length=1)
    last_name = models.CharField(_("Last Name"), max_length=50)
    phone_number = PhoneNumberField(_("Phone Number"))
    address = models.CharField(_("Address Line 1"), max_length=100)

    credit_limit = models.DecimalField(_("Account Credit Limit"), decimal_places=2, max_digits=12)
    balance = models.DecimalField(_("Current Account Balance"), decimal_places=2, max_digits=12)
    open_to_buy = models.DecimalField(_("Current Available Credit"), decimal_places=2, max_digits=12)

    last_payment_date = models.DateField(_("Last Payment Date"), null=True)
    last_payment_amount = models.DecimalField(_("Last Payment Amount"), decimal_places=2, max_digits=12, null=True)

    payment_due_date = models.DateField(_("Payment Due Date"), null=True)
    payment_due_amount = models.DecimalField(_("Payment Due on Account"), decimal_places=2, max_digits=12, null=True)

    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_datetime', '-id')

    @property
    def full_name(self):
        return '{} {} {}'.format(self.first_name, self.middle_initial, self.last_name)

    @property
    def masked_account_number(self):
        return 'xxxxxxxxxxxx{}'.format(self.last4_account_number)

    @property
    def account_number(self):
        if self._full_account_number:
            return self._full_account_number
        return self.masked_account_number

    @account_number.setter
    def account_number(self, value):
        if len(value) != 16:
            raise ValueError('Account number must be 16 digits long')
        self.last4_account_number = value[-4:]
        self._full_account_number = value



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
    def get_by_oscar_transaction(cls, transaction, type_code=TRANS_TYPE_AUTH):
        return cls.objects.filter(merchant_reference=transaction.reference)\
                          .filter(type_code=type_code)\
                          .order_by('-created_datetime')\
                          .first()

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
        Transaction = get_model('payment', 'Transaction')
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



class CreditAppCommonMixin(models.Model):
    credentials = models.ForeignKey(APICredentials,
        null=True, blank=True,
        verbose_name=_("Merchant"),
        help_text=_("Which merchant account submitted this application?"),
        related_name='+',
        on_delete=models.SET_NULL)
    application_source = models.CharField(_("Application Source"), default='Website', max_length=25,
        help_text=_("Where/how is user applying? E.g. Website, Call Center, In-Store, etc."))
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Owner"),
        help_text=_("Select the user user who is applying and who will own (be the primary user of) this account."),
        related_name='+',
        on_delete=models.SET_NULL)
    submitting_user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Submitting User"),
        help_text=_("Select the user who filled out and submitted the credit application (not always the same as the user who is applying for credit)."),
        related_name='+',
        on_delete=models.SET_NULL)
    inquiries = models.ManyToManyField(AccountInquiryResult,
        verbose_name=_("Account Inquiries"),
        related_name='+')

    _orders_cache = None
    _first_order_cache = None

    class Meta:
        abstract = True


    def get_credit_limit(self):
        inquiry = self.inquiries.order_by('-created_datetime').first()
        if not inquiry:
            return None
        return inquiry.credit_limit


    def get_orders(self):
        """
        Find orders that were probably placed using the account that resulted from this application. It's
        not foolproof since we don't store the full account number.
        """
        if not self._orders_cache:
            Order = get_model('order', 'Order')
            reference_uuids = set(TransferMetadata.objects.filter(last4_account_number=self.last4_account_number)
                                                          .values_list('merchant_reference', flat=True)
                                                          .distinct()
                                                          .all())
            orders = Order.objects.filter(Q(guest_email=self.email) | Q(user__email=self.email))\
                                  .filter(sources__transactions__reference__in=reference_uuids)\
                                  .order_by('date_placed')\
                                  .all()
            self._orders_cache = orders
        return self._orders_cache


    def get_first_order(self):
        if not self._first_order_cache:
            self._first_order_cache = self.get_orders().first()
        return self._first_order_cache



class USCreditApp(CreditAppCommonMixin, USCreditAppMixin, BaseCreditAppMixin):
    APP_TYPE_CODE = 'us-individual'



class USJointCreditApp(CreditAppCommonMixin, USJointCreditAppMixin, BaseJointCreditAppMixin):
    APP_TYPE_CODE = 'us-joint'



class CACreditApp(CreditAppCommonMixin, CACreditAppMixin, BaseCreditAppMixin):
    APP_TYPE_CODE = 'ca-individual'



class CAJointCreditApp(CreditAppCommonMixin, CAJointCreditAppMixin, BaseJointCreditAppMixin):
    APP_TYPE_CODE = 'ca-joint'



class PreQualificationRequest(models.Model):
    locale = models.CharField(_('Locale'),
        max_length=_max_len(PREQUAL_LOCALE_CHOICES),
        choices=PREQUAL_LOCALE_CHOICES,
        default=EN_US)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    entry_point = models.CharField(_('Entry Point'),
        max_length=_max_len(ENTRY_POINT_CHOICES),
        choices=ENTRY_POINT_CHOICES,
        default=ENTRY_POINT_WEB)
    first_name = models.CharField(_("First Name"), max_length=15)
    last_name = models.CharField(_("Last Name"), max_length=20)
    line1 = models.CharField(_("Address Line 1"), max_length=26)
    city = models.CharField(_("City"), max_length=15)
    state = USStateField(_("State"))
    postcode = USZipCodeField(_("Postcode"))
    phone = PhoneNumberField(_("Phone"))
    credentials = models.ForeignKey(APICredentials,
        verbose_name=_("API Credentials"),
        related_name='prequal_requests',
        null=True, blank=True,
        on_delete=models.SET_NULL)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_datetime', '-id')

    @property
    def locale_name(self):
        return dict(PREQUAL_LOCALE_CHOICES).get(self.locale, self.locale)

    @property
    def entry_point_name(self):
        return dict(ENTRY_POINT_CHOICES).get(self.entry_point, self.entry_point)


class PreQualificationResponse(models.Model):
    request = models.OneToOneField(PreQualificationRequest, related_name='response', on_delete=models.CASCADE)
    status = models.CharField(_('Transaction Status'),
        max_length=_max_len(PREQUAL_TRANS_STATUS_CHOICES),
        choices=PREQUAL_TRANS_STATUS_CHOICES)
    message = models.TextField(_('Message'))
    offer_indicator = models.CharField(_('Offer Indicator'), max_length=20)
    credit_limit = models.DecimalField(_("Credit Limit"), decimal_places=2, max_digits=12)
    response_id = models.CharField(_('Unique Response ID'), max_length=8)
    application_url = models.CharField(_('Application URL'), max_length=200)
    customer_response = models.CharField(_('Customer Response'),
        max_length=_max_len(PREQUAL_CUSTOMER_RESP_CHOICES),
        choices=PREQUAL_CUSTOMER_RESP_CHOICES,
        default=PREQUAL_CUSTOMER_RESP_NONE)
    customer_order = models.ForeignKey('order.Order',
        null=True, blank=True,
        related_name='prequalification_responses',
        on_delete=models.CASCADE)
    reported_datetime = models.DateTimeField(null=True, blank=True,
        help_text=_('Date customer response was reported to Wells Fargo.'))
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_datetime', '-id')


    @property
    def is_approved(self):
        return self.status == PREQUAL_TRANS_STATUS_APPROVED


    @property
    def status_name(self):
        return dict(PREQUAL_TRANS_STATUS_CHOICES).get(self.status, self.status)


    @property
    def customer_response_name(self):
        return dict(PREQUAL_CUSTOMER_RESP_CHOICES).get(self.customer_response, self.customer_response)


    @property
    def full_application_url(self):
        # Take the given base URL and append a query param with the last 10 digits of the merchant account number
        merchant_num = self.request.credentials.merchant_num[-10:]
        return "{base_url}&mn={merchant_num}".format(
            base_url=self.application_url,
            merchant_num=merchant_num)


    def check_account_status(self):
        from .connector import actions
        return actions.check_pre_qualification_account_status(self)
