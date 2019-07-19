from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_model
from oscar.models.fields import PhoneNumberField
from ..core.constants import (
    CREDIT_APP_STATUSES,
    INQUIRY_STATUSES,
)
from ..core.applications import (
    USCreditAppMixin,
    BaseCreditAppMixin,
    USJointCreditAppMixin,
    BaseJointCreditAppMixin,
    CACreditAppMixin,
    CAJointCreditAppMixin,
)
from .mixins import AccountNumberMixin
from .creds import APICredentials
from .transfers import TransferMetadata
from .utils import _max_len



class AccountInquiryResult(AccountNumberMixin, models.Model):
    credit_app_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    credit_app_id = models.PositiveIntegerField(null=True, blank=True)
    credit_app_source = GenericForeignKey('credit_app_type', 'credit_app_id')

    prequal_response_source = models.ForeignKey('wellsfargo.PreQualificationResponse',
        verbose_name=_("Pre-Qualification Source"),
        related_name='account_inquiries',
        null=True, blank=True,
        on_delete=models.SET_NULL)

    status = models.CharField(_("Status"), choices=INQUIRY_STATUSES, max_length=2)

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
        verbose_name = _('Account Inquiry Result')
        verbose_name_plural = _('Account Inquiry Results')

    @property
    def full_name(self):
        # Translators: Assemble name pieces into full name
        return _('%(first_name)s %(middle_initial)s %(last_name)s') % dict(
            first_name=self.first_name,
            middle_initial=self.middle_initial,
            last_name=self.last_name)



class CreditAppCommonMixin(models.Model):
    status = models.CharField(_('Application Status'),
        max_length=_max_len(CREDIT_APP_STATUSES),
        choices=CREDIT_APP_STATUSES,
        default='')
    credentials = models.ForeignKey(APICredentials,
        null=True, blank=True,
        verbose_name=_("Merchant"),
        help_text=_("Which merchant account submitted this application?"),
        related_name='+',
        on_delete=models.SET_NULL)
    application_source = models.CharField(_("Application Source"), default=_('Website'), max_length=25,
        help_text=_("Where/how is user applying? E.g. Website, Call Center, In-Store, etc."))
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Owner"),
        help_text=_("Select the user user who is applying and who will own (be the primary user of) this account."),
        related_name='+',
        on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    submitting_user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Submitting User"),
        help_text=_("Select the user who filled out and submitted the credit application (not always the same as the user who is applying for credit)."),
        related_name='+',
        on_delete=models.SET_NULL)
    inquiries = GenericRelation(AccountInquiryResult,
        content_type_field='credit_app_type',
        object_id_field='credit_app_id')

    class Meta:
        abstract = True


    def get_inquiries(self):
        return self.inquiries.order_by('-created_datetime').all()


    def get_credit_limit(self):
        inquiry = self.get_inquiries().first()
        if not inquiry:
            return None
        return inquiry.credit_limit


    def get_orders(self):
        """
        Find orders that were probably placed using the account that resulted from this application. It's
        not foolproof since we don't store the full account number.
        """
        if not hasattr(self, '_orders_cache'):
            Order = get_model('order', 'Order')
            # all transfers made with last 4 digits
            reference_uuids = set(TransferMetadata.objects.filter(last4_account_number=self.last4_account_number)
                                                          .values_list('merchant_reference', flat=True)
                                                          .distinct()
                                                          .all())
            # all orders made by app.email that contain ref above UUIDs
            orders = Order.objects.filter(Q(guest_email=self.email) | Q(user__email=self.email))\
                                  .filter(sources__transactions__reference__in=reference_uuids)\
                                  .filter(date_placed__gte=self.created_datetime)\
                                  .order_by('date_placed')\
                                  .all()
            self._orders_cache = orders
        return self._orders_cache


    def get_first_order(self):
        if not hasattr(self, '_first_order_cache'):
            self._first_order_cache = self.get_orders().first()
        return self._first_order_cache


    def get_first_order_merchant(self):
        Transaction = get_model('payment', 'Transaction')
        order = self.get_first_order()
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
        return transfers[0].credentials



class USCreditApp(CreditAppCommonMixin, USCreditAppMixin, BaseCreditAppMixin):
    APP_TYPE_CODE = 'us-individual'

    class Meta:
        verbose_name = _('US Individual Credit Application')
        verbose_name_plural = _('US Individual Credit Applications')



class USJointCreditApp(CreditAppCommonMixin, USJointCreditAppMixin, BaseJointCreditAppMixin):
    APP_TYPE_CODE = 'us-joint'

    class Meta:
        verbose_name = _('US Joint Credit Application')
        verbose_name_plural = _('US Joint Credit Applications')



class CACreditApp(CreditAppCommonMixin, CACreditAppMixin, BaseCreditAppMixin):
    APP_TYPE_CODE = 'ca-individual'

    class Meta:
        verbose_name = _('CA Individual Credit Application')
        verbose_name_plural = _('CA Individual Credit Applications')



class CAJointCreditApp(CreditAppCommonMixin, CAJointCreditAppMixin, BaseJointCreditAppMixin):
    APP_TYPE_CODE = 'ca-joint'

    class Meta:
        verbose_name = _('CA Joint Credit Application')
        verbose_name_plural = _('CA Joint Credit Applications')
