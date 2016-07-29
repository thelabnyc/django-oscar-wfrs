from django.utils.translation import ugettext as _
from django import template

register = template.Library()


@register.filter(name='timeat')
def timeat(value):
    try:
        return _('%s years, %s months') % (int(value[2:]), int(value[:2]))
    except:
        return ""
