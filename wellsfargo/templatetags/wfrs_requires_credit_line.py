from django import template
from ..models import FinancingPlan

register = template.Library()


@register.simple_tag
def get_requires_credit_line():
    return FinancingPlan.objects.filter(requires_credit_line=True).first()
