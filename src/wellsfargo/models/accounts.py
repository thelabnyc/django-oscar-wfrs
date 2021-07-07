from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.models.fields import NullCharField
from .mixins import AccountNumberMixin


class AccountInquiryResult(AccountNumberMixin, models.Model):
    credit_app_source = models.ForeignKey(
        "wellsfargo.CreditApplication",
        verbose_name=_("Credit Application Source"),
        related_name="inquiries",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    prequal_response_source = models.ForeignKey(
        "wellsfargo.PreQualificationResponse",
        verbose_name=_("Pre-Qualification Source"),
        related_name="inquiries",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    main_applicant_full_name = NullCharField(_("Main Applicant Name"), max_length=50)
    joint_applicant_full_name = NullCharField(_("Joint Applicant Name"), max_length=50)

    main_applicant_address = models.ForeignKey(
        "wellsfargo.CreditApplicationAddress",
        verbose_name=_("Main Applicant Address"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    joint_applicant_address = models.ForeignKey(
        "wellsfargo.CreditApplicationAddress",
        verbose_name=_("Joint Applicant Address"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    credit_limit = models.DecimalField(
        _("Account Credit Limit"), decimal_places=2, max_digits=12
    )
    available_credit = models.DecimalField(
        _("Current Available Credit"), decimal_places=2, max_digits=12
    )

    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_datetime", "-id")
        verbose_name = _("Account Inquiry Result")
        verbose_name_plural = _("Account Inquiry Results")
