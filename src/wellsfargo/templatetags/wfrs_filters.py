from django.utils.translation import ugettext as _
from django import template
import pytz


register = template.Library()


@register.filter(name="timeat")
def timeat(value):
    try:
        return _("%(years)s years, %(months)s months") % dict(
            years=int(value[2:]), months=int(value[:2])
        )
    except Exception:
        return ""


@register.filter(name="timesinceminutes")
def timesinceminutes(dt_to, dt_from):
    if not dt_to or not dt_from:
        return ""
    return round((dt_to - dt_from).total_seconds() / 60)


@register.filter(name="localizedatetime")
def localizedatetime(value):
    if not value:
        return ""
    return pytz.utc.localize(value)
