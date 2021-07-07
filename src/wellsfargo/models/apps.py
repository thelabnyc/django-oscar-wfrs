from django.conf import settings
from django.db import models
from django.db.models import Q
from django.core.validators import (
    MinLengthValidator,
    MaxLengthValidator,
    MinValueValidator,
    MaxValueValidator,
)
from django.utils.translation import gettext_lazy as _
from localflavor.us.models import (
    USStateField,
    USZipCodeField,
)
from oscar.core.loading import get_model
from oscar.models.fields import PhoneNumberField, NullCharField
from ..core.constants import (
    CREDIT_APP_STATUSES,
    HOUSING_STATUSES,
    CREDIT_APP_TRANS_CODES,
    CREDIT_APP_TRANS_CODE_CREDIT_APPLICATION,
    LANGUAGES,
    ENGLISH,
)
from ..core.fields import (
    USSocialSecurityNumberField,
    DateOfBirthField,
)
from .mixins import MaybeAccountNumberMixin
from .transfers import TransferMetadata
from .utils import _max_len


class CreditApplicationAddress(models.Model):
    address_line_1 = models.CharField(_("Address Line 1"), max_length=26)
    address_line_2 = NullCharField(_("Address Line 2"), max_length=26)
    city = models.CharField(_("City"), max_length=18)
    state_code = USStateField(_("State"))
    postal_code = USZipCodeField(
        _("Postcode"), validators=[MinLengthValidator(5), MaxLengthValidator(5)]
    )


class CreditApplicationApplicant(models.Model):
    first_name = models.CharField(_("First Name"), max_length=15)
    last_name = models.CharField(_("Last Name"), max_length=20)
    middle_initial = NullCharField(_("Middle Initial"), max_length=1)
    date_of_birth = DateOfBirthField(_("Date of Birth"))
    ssn = USSocialSecurityNumberField(_("Social Security Number"))
    annual_income = models.IntegerField(
        _("Annual Income"), validators=[MinValueValidator(0), MaxValueValidator(999999)]
    )
    email_address = models.EmailField(
        _("Email"),
        max_length=50,
        null=True,
        blank=True,
        validators=[MinLengthValidator(7)],
    )
    home_phone = PhoneNumberField(_("Home Phone"))
    mobile_phone = PhoneNumberField(_("Mobile Phone"), null=True, blank=True)
    work_phone = PhoneNumberField(_("Work Phone"), null=True, blank=True)
    employer_name = NullCharField(_("Employer Name"), max_length=30)
    housing_status = NullCharField(
        _("Housing Status"),
        max_length=_max_len(HOUSING_STATUSES),
        choices=HOUSING_STATUSES,
    )
    address = models.ForeignKey(
        "wellsfargo.CreditApplicationAddress",
        verbose_name=_("Address"),
        related_name="+",
        on_delete=models.CASCADE,
    )


class CreditApplication(MaybeAccountNumberMixin, models.Model):
    transaction_code = models.CharField(
        _("Transaction Code"),
        max_length=_max_len(CREDIT_APP_TRANS_CODES),
        choices=CREDIT_APP_TRANS_CODES,
        default=CREDIT_APP_TRANS_CODE_CREDIT_APPLICATION,
        help_text=_("Indicates where the transaction takes place."),
    )
    reservation_number = NullCharField(
        _("Reservation Number"),
        max_length=20,
        help_text=_("The unique code that correlates with the user’s reservation."),
    )
    application_id = NullCharField(
        _("Prequalified Application ID"),
        max_length=8,
        help_text=_("An 8-character alphanumeric ID identifying the application."),
    )
    requested_credit_limit = models.IntegerField(
        _("Requested Credit Limit"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(99999)],
        help_text=_(
            "This denotes the total price value of the items that the applicant’s shopping cart."
        ),
    )
    language_preference = models.CharField(
        _("Language Preference"),
        max_length=_max_len(LANGUAGES),
        choices=LANGUAGES,
        default=ENGLISH,
        help_text=_("The main applicant’s language preference values"),
    )
    salesperson = NullCharField(
        _("Sales Person ID"),
        max_length=10,
        help_text=_("Alphanumeric value associated with the salesperson."),
    )

    # Main applicant data
    main_applicant = models.ForeignKey(
        "wellsfargo.CreditApplicationApplicant",
        verbose_name=_("Main Applicant"),
        related_name="+",
        on_delete=models.CASCADE,
        help_text=_("The main applicant’s personal details."),
    )
    joint_applicant = models.ForeignKey(
        "wellsfargo.CreditApplicationApplicant",
        verbose_name=_("Joint Applicant"),
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.CASCADE,
        help_text=_("The joint applicant’s details."),
    )

    # Submit Status
    status = models.CharField(
        _("Application Status"),
        max_length=_max_len(CREDIT_APP_STATUSES),
        choices=CREDIT_APP_STATUSES,
        default="",
        help_text=_("Application Status"),
    )

    # Internal Metadata
    merchant_name = NullCharField(_("Merchant Name"), max_length=200)
    merchant_num = NullCharField(_("Merchant Number"), max_length=200)
    application_source = models.CharField(
        _("Application Source"),
        default=_("Website"),
        max_length=25,
        help_text=_(
            "Where/how is user applying? E.g. Website, Call Center, In-Store, etc."
        ),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        verbose_name=_("Owner"),
        help_text=_(
            "Select the user user who is applying and who will own (be the primary user of) this account."
        ),
        related_name="+",
        on_delete=models.SET_NULL,
    )
    ip_address = models.GenericIPAddressField(
        _("Submitting User's IP Address"),
        null=True,
        blank=True,
        help_text=_("Submitting User's IP Address"),
    )
    submitting_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        verbose_name=_("Submitting User"),
        help_text=_(
            "Select the user who filled out and submitted the credit application (not always the same as the user who is applying for credit)."
        ),
        related_name="+",
        on_delete=models.SET_NULL,
    )
    created_datetime = models.DateTimeField(_("Created Date/Time"), auto_now_add=True)
    modified_datetime = models.DateTimeField(_("Modified Date/Time"), auto_now=True)

    class Meta:
        verbose_name = _("Wells Fargo Credit Application")
        verbose_name_plural = _("Wells Fargo Credit Applications")

    @property
    def is_joint(self):
        return False

    @property
    def full_name(self):
        return "%s %s" % (self.main_applicant.first_name, self.main_applicant.last_name)

    def get_inquiries(self):
        return self.inquiries.order_by("-created_datetime").all()

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
        if not hasattr(self, "_orders_cache"):
            Order = get_model("order", "Order")
            # all transfers made with last 4 digits
            reference_uuids = set(
                TransferMetadata.objects.filter(
                    last4_account_number=self.last4_account_number
                )
                .values_list("merchant_reference", flat=True)
                .distinct()
                .all()
            )
            # all orders made by app.email that contain ref above UUIDs
            emails = [self.main_applicant.email_address]
            if self.joint_applicant:
                emails.append(self.joint_applicant.email_address)
            orders = (
                Order.objects.filter(
                    Q(guest_email__in=emails) | Q(user__email__in=emails)
                )
                .filter(sources__transactions__reference__in=reference_uuids)
                .filter(date_placed__gte=self.created_datetime)
                .order_by("date_placed")
                .all()
            )
            self._orders_cache = orders
        return self._orders_cache

    def get_first_order(self):
        if not hasattr(self, "_first_order_cache"):
            self._first_order_cache = self.get_orders().first()
        return self._first_order_cache

    def get_first_order_merchant_name(self):
        Transaction = get_model("payment", "Transaction")
        order = self.get_first_order()
        if not order:
            return None
        transfers = []
        for source in order.sources.filter(source_type__name="Wells Fargo").all():
            for transaction in source.transactions.filter(
                txn_type=Transaction.AUTHORISE
            ).all():
                transfer = TransferMetadata.get_by_oscar_transaction(transaction)
                if transfer:
                    transfers.append(transfer)
        if len(transfers) <= 0:
            return None
        return transfers[0].merchant_name
