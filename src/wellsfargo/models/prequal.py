from django.core import signing
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property
from oscar.core.loading import get_model
from oscar.models.fields import PhoneNumberField
from ..core.constants import (
    EN_US,
    PREQUAL_LOCALE_CHOICES,
    ENTRY_POINT_WEB,
    ENTRY_POINT_CHOICES,
    PREQUAL_TRANS_STATUS_APPROVED,
    PREQUAL_TRANS_STATUS_REJECTED,
    PREQUAL_TRANS_STATUS_CHOICES,
    PREQUAL_CUSTOMER_RESP_NONE,
    PREQUAL_CUSTOMER_RESP_CHOICES,
    get_prequal_trans_status_name,
)
from ..core.fields import USStateField, USZipCodeField
from .creds import APICredentials
from .transfers import TransferMetadata
from .utils import _max_len
import uuid
import urllib.parse



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
    customer_initiated = models.BooleanField(_("Check was deliberately initiated by customer action"), default=False)
    email = models.EmailField(_("Email"), null=True, blank=True)
    first_name = models.CharField(_("First Name"), max_length=15)
    middle_initial = models.CharField(_("Middle Initial"), null=True, blank=True, max_length=1)
    last_name = models.CharField(_("Last Name"), max_length=20)
    line1 = models.CharField(_("Address Line 1"), max_length=26)
    line2 = models.CharField(_("Address Line 2"), max_length=26, null=True, blank=True)
    city = models.CharField(_("City"), max_length=15)
    state = USStateField(_("State"))
    postcode = USZipCodeField(_("Postcode"))
    phone = PhoneNumberField(_("Phone"))
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    credentials = models.ForeignKey(APICredentials,
        verbose_name=_("API Credentials"),
        related_name='prequal_requests',
        null=True, blank=True,
        on_delete=models.SET_NULL)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Pre-Qualification Request')
        verbose_name_plural = _('Pre-Qualification Requests')
        ordering = ('-created_datetime', '-id')
        indexes = [
            models.Index(fields=['-created_datetime', '-id']),
        ]


    @property
    def locale_name(self):
        return dict(PREQUAL_LOCALE_CHOICES).get(self.locale, self.locale)


    @property
    def entry_point_name(self):
        return dict(ENTRY_POINT_CHOICES).get(self.entry_point, self.entry_point)


    @property
    def status(self):
        response = getattr(self, 'response', None)
        if response:
            return response.status
        return PREQUAL_TRANS_STATUS_REJECTED


    @property
    def status_name(self):
        response = getattr(self, 'response', None)
        if response:
            return response.status_name
        return get_prequal_trans_status_name(PREQUAL_TRANS_STATUS_REJECTED, self.customer_initiated)


    @property
    def merchant_name(self):
        return self.credentials.name if self.credentials else None


    @property
    def merchant_num(self):
        return self.credentials.merchant_num if self.credentials else None


    @property
    def credit_limit(self):
        resp = getattr(self, 'response', None)
        if resp is None:
            return None
        return resp.credit_limit


    @property
    def customer_response(self):
        resp = getattr(self, 'response', None)
        if resp is None:
            return None
        return resp.customer_response


    @property
    def sdk_application_result(self):
        resp = getattr(self, 'response', None)
        if resp is None:
            return None
        app_result = getattr(resp, 'sdk_application_result', None)
        if app_result is None:
            return None
        return app_result.application_status


    @cached_property
    def resulting_order(self):
        resp = getattr(self, 'response', None)
        if resp and resp.customer_order:
            return resp.customer_order
        # Look for other orders which might have been placed by this customer
        Order = get_model('order', 'Order')
        email_matches = Q(guest_email=self.email) | Q(user__email=self.email)
        date_matches = Q(date_placed__gt=self.created_datetime)
        order = Order.objects.filter(email_matches & date_matches)\
                             .order_by('date_placed')\
                             .first()
        return order


    @property
    def order_total(self):
        return self.resulting_order.total_incl_tax if self.resulting_order else None


    @property
    def order_date_placed(self):
        return self.resulting_order.date_placed if self.resulting_order else None


    @cached_property
    def order_merchant_name(self):
        Transaction = get_model('payment', 'Transaction')
        order = self.resulting_order
        if not order:
            return None
        transfers = []
        for source in order.sources.filter(source_type__name='Wells Fargo').all():
            for transaction in source.transactions.filter(txn_type=Transaction.AUTHORISE).all():
                transfer = TransferMetadata.get_by_oscar_transaction(transaction)
                if transfer:
                    transfers.append(transfer)
        if len(transfers) <= 0:
            return None
        credentials = transfers[0].credentials
        return credentials.name if credentials else None


    @property
    def response_reported_datetime(self):
        resp = getattr(self, 'response', None)
        if resp is None:
            return None
        return resp.reported_datetime


    def get_signed_id(self):
        return signing.Signer().sign(self.pk)


    def get_resume_offer_url(self, next_url='/'):
        url = reverse('wfrs-api-prequal-resume', args=[self.get_signed_id()])
        qs = urllib.parse.urlencode({
            'next': next_url,
        })
        return '{}?{}'.format(url, qs)



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
        verbose_name = _('Pre-Qualification Response')
        verbose_name_plural = _('Pre-Qualification Responses')
        ordering = ('-created_datetime', '-id')


    @property
    def is_approved(self):
        return self.status == PREQUAL_TRANS_STATUS_APPROVED


    @property
    def status_name(self):
        return get_prequal_trans_status_name(self.status, self.request.customer_initiated)


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
        from ..connector import actions
        return actions.check_pre_qualification_account_status(self)



class PreQualificationSDKApplicationResult(models.Model):
    prequal_response = models.OneToOneField(PreQualificationResponse,
        verbose_name=_('PreQualification Response'),
        related_name='sdk_application_result',
        null=True, blank=True,
        on_delete=models.SET_NULL)
    application_id = models.CharField(_('Unique Response ID'), max_length=8)
    first_name = models.CharField(_("First Name"), max_length=15)
    last_name = models.CharField(_("Last Name"), max_length=20)
    application_status = models.CharField(_("Application Status"), max_length=20)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Pre-Qualification SDK Application Result')
        verbose_name_plural = _('Pre-Qualification SDK Application Results')
