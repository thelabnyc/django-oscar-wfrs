from decimal import Decimal
from django.core import exceptions
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import get_model, get_class

Benefit = get_model('offer', 'Benefit')
HiddenPostOrderAction = get_class('offer.results', 'HiddenPostOrderAction')



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
        verbose_name = _('Financing Plan')
        verbose_name_plural = _('Financing Plans')


    @classmethod
    def get_advertisable_plan_by_price(cls, price):
        plan = cls.objects\
            .exclude(term_months=0)\
            .filter(advertising_enabled=True)\
            .filter(product_price_threshold__gte='0.00')\
            .filter(product_price_threshold__lte=price)\
            .order_by('-product_price_threshold', '-apr')\
            .first()
        return plan


    def __str__(self):
        return _("%(description)s (plan number %(number)s)") % dict(
            description=self.description,
            number=self.plan_number)

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
        verbose_name = _('Financing Plan Benefit')
        verbose_name_plural = _('Financing Plan Benefits')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy_class = 'wellsfargo.models.%s' % self.__class__.__name__

    def __str__(self):
        return self.group_name

    def apply(self, basket, condition, offer):
        condition.consume_items(offer, basket, [])
        return HiddenPostOrderAction(_("Financing is available for your order"))

    def apply_deferred(self, basket, order, application):
        return _("Financing was available for your order: %s") % self.group_name

    @property
    def name(self):
        return self.group_name

    @property
    def description(self):
        nums = ', '.join([str(p.plan_number) for p in self.plans.all()])
        return _("Causes the following Wells Fargo financing plans to be available: %s") % nums

    def _clean(self):
        group_name = getattr(self, 'group_name', None)
        if not group_name:
            raise exceptions.ValidationError(_((
                "Wells Fargo Financing Plan Benefit must have a group name. "
                "Use the Financing > Wells Fargo Plan Group dashboard to create this type of benefit."
            )))
