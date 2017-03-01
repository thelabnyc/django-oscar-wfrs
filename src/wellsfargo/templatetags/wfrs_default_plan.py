from django import template
from ..models import FinancingPlan

register = template.Library()


@register.simple_tag
def get_default_plan():
    return FinancingPlan.objects.filter(is_default_plan=True).first()
