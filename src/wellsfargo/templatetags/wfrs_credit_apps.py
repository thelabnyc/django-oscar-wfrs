from django import template
from django.utils.translation import gettext_lazy as _
from django_tables2 import RequestConfig
from ..models import CreditApplication
from ..dashboard.tables import CreditApplicationTable

register = template.Library()


@register.simple_tag
def get_credit_apps_owned_by_user(user):
    return CreditApplication.objects.filter(user=user).all()


@register.simple_tag(takes_context=True)
def get_table_for_applications(context, prefix, applications):
    table = CreditApplicationTable(applications, prefix=prefix)
    table.caption = _('Credit Applications')
    paginate = {
        'per_page': 25
    }
    RequestConfig(context.request, paginate=paginate).configure(table)
    return table
