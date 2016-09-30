from django.forms.widgets import Widget, Select, Input
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.forms.utils import flatatt


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
        local_attrs = self.build_attrs(id=field % id_)
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

    def render(self, name, value, attrs=None, choices=()):
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
        return super().render(name, value, attrs, choices)

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



class TypeAheadModelSelect(Input):
    def __init__(self, view, model, attrs=None):
        self.view = view
        self.model = model
        super().__init__(attrs)


    def render(self, name, value, attrs=None):
        url = '%s?term=' % reverse(self.view)
        wildcard = '%Q'

        if value is None:
            value = ''

        attrs_auto = self.build_attrs(attrs, type='text', name=name)
        attrs_hidden = self.build_attrs(attrs, type='hidden', name=name)
        if value != '':
            attrs_hidden['value'] = force_text(value)
        if attrs_hidden.get('value'):
            attrs_auto['value'] = force_text(self.model.objects.filter(pk=attrs_hidden['value']).first() or '')
        attrs_auto['autocomplete'] = 'none'
        attrs_auto['id'] += '_auto'

        html = format_html('<input{} />', flatatt(attrs_auto))
        html += format_html('<input{} />', flatatt(attrs_hidden))
        html += """
            <style type="text/css">
                .twitter-typeahead {
                    width: 100%;
                }
                .typeahead,
                .tt-query,
                .tt-hint {
                    width: 100%;
                    height: 34px;
                    padding: 8px 12px;
                    font-size: 24px;
                    line-height: 30px;
                    border: 2px solid #ccc;
                    outline: none;
                }

                .typeahead {
                    background-color: #fff;
                }

                .typeahead:focus {
                    border: 2px solid #0097cf;
                }

                .tt-query {
                    -webkit-box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.075);
                       -moz-box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.075);
                            box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.075);
                }

                .tt-hint {
                    color: #999
                }

                .tt-menu {
                    width: 100%;
                    margin: 12px 0;
                    padding: 8px 0;
                    background-color: #fff;
                    border: 1px solid #CCC;
                    -webkit-box-shadow: 0 5px 10px rgba(0,0,0,.2);
                       -moz-box-shadow: 0 5px 10px rgba(0,0,0,.2);
                            box-shadow: 0 5px 10px rgba(0,0,0,.2);
                }

                .tt-suggestion {
                    padding: 3px 20px;
                    font-size: 18px;
                    line-height: 24px;
                }

                .tt-suggestion:hover {
                    cursor: pointer;
                    color: #fff;
                    background-color: #0097cf;
                }

                .tt-suggestion.tt-cursor {
                    color: #fff;
                    background-color: #0097cf;
                }

                .tt-suggestion p {
                    margin: 0;
                }
            </style>
            <script type="text/javascript">
                document.body.onload = function() {
                    var source = new Bloodhound({
                        datumTokenizer: Bloodhound.tokenizers.obj.whitespace('label'),
                        queryTokenizer: Bloodhound.tokenizers.whitespace,
                        remote: {
                            url: '""" + url + wildcard + """',
                            wildcard: '""" + wildcard + """'
                        }
                    });

                    var auto = $('#""" + attrs_auto['id'] + """');
                    var hidden = $('#""" + attrs_hidden['id'] + """');

                    auto.typeahead(null, {
                        name: '""" + name + """',
                        display: 'label',
                        source: source
                    });

                    auto.bind('typeahead:select', function(event, selected) {
                        hidden.val(selected.id);
                    });
                };
            </script>
        """
        return mark_safe(html)
