from django.forms.widgets import Widget, Select
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class FuzzyDurationWidget(Widget):
    """
    A Widget that allows selection of a duration of time using two selects,
    one for months and years, respectively.
    """
    month_field = '%s_month'
    year_field = '%s_year'
    select_widget = Select

    def __init__(self, attrs=None, max_years=100):
        self.attrs = attrs or {}
        self.years = range(0, max_years)
        self.months = range(0, 12)

    def render(self, name, value, attrs=None):
        if value and isinstance(value, str) and len(value) == 4:
            month_val = int(value[:2])
            year_val = int(value[2:])
        else:
            month_val = None
            year_val = None

        choices = [(i, i) for i in self.months]
        months = self.create_select(name, self.month_field, value, month_val, choices)

        choices = [(i, i) for i in self.years]
        years = self.create_select(name, self.year_field, value, year_val, choices)

        html = """
            <table class='fuzzy-duration'>
                <tr>
                    <td>""" + years + """</td>
                    <td>""" + months + """</td>
                </tr>
                <tr>
                    <th>""" + str(_('Years')) + """</th>
                    <th>""" + str(_('Months')) + """</th>
                </tr>
            </table>"""
        return mark_safe(html)

    def id_for_label(self, id_):
        return '%s_month' % id_

    def value_from_datadict(self, data, files, name):
        m = data.get(self.month_field % name, '').zfill(2)
        y = data.get(self.year_field % name, '').zfill(2)
        return "%s%s" % (m, y)

    def create_select(self, name, field, value, val, choices):
        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name
        local_attrs = self.build_attrs(dict(id=field % id_))
        s = self.select_widget(choices=choices)
        select_html = s.render(field % name, val, local_attrs)
        return select_html



class BooleanSelect(Select):
    def __init__(self, attrs=None):
        choices = (
            ('0', _('No')),
            ('1', _('Yes')),
        )
        super().__init__(attrs, choices)

    def render(self, name, value, attrs=None):
        try:
            mapping = {
                False: '0',
                True: '1',
                '0': '0',
                '1': '1',
            }
            value = mapping[value]
        except KeyError:
            value = '0'
        return super().render(name, value, attrs)

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        mapping = {
            '0': False,
            'False': False,
            False: False,
            '1': True,
            'True': True,
            True: True,
        }
        return mapping.get(value)
