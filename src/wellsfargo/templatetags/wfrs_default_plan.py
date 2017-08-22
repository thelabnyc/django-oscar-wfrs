from django import template
from ..models import FinancingPlan

register = template.Library()


@register.simple_tag
def get_default_plan():
    return FinancingPlan.objects.filter(advertising_enabled=True, is_default_plan=True).first()


@register.simple_tag
def get_plan_for_product(request, product):
    if product.is_parent:
        purchase_info = request.strategy.fetch_for_parent(product)
    else:
        purchase_info = request.strategy.fetch_for_product(product)
    if purchase_info.price.is_tax_known:
        price = purchase_info.price.incl_tax
    else:
        price = purchase_info.price.excl_tax
    return FinancingPlan.objects\
        .filter(advertising_enabled=True)\
        .filter(product_price_threshold__gte='0.00')\
        .filter(product_price_threshold__lte=price)\
        .order_by('-product_price_threshold')\
        .first()


@register.simple_tag
def get_monthly_price(plan, price):
    if plan.term_months <= 0:
        return None
    return (price / plan.term_months).quantize(price)
