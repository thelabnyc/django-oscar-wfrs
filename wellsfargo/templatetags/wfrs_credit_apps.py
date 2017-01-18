from django import template
from django.utils.translation import ugettext_lazy as _
from django_tables2 import RequestConfig
from haystack.query import SearchQuerySet
from haystack.inputs import Exact
from ..models import USCreditApp, USJointCreditApp, CACreditApp, CAJointCreditApp
from ..dashboard.tables import CreditApplicationIndexTable

register = template.Library()


@register.simple_tag
def get_credit_apps_owned_by_user(user):
    qs = SearchQuerySet()\
        .models(USCreditApp, USJointCreditApp, CACreditApp, CAJointCreditApp)\
        .filter(user_id=Exact(user.pk))
    return qs.all()


@register.simple_tag(takes_context=True)
def get_table_for_applications(context, prefix, applications):
    table = CreditApplicationIndexTable(applications, prefix=prefix)
    table.caption = _('Credit Applications')
    paginate = {
        'per_page': 25
    }
    RequestConfig(context.request, paginate=paginate).configure(table)
    return table
