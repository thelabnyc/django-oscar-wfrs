from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from oscar.forms.widgets import DatePickerInput
from .widgets import FuzzyDurationWidget, BooleanSelect
from ..core.constants import (
    US, CA,
    INDIVIDUAL, JOINT,
    LOCALES,
    APP_TYPES, LANGUAGES, REGIONS
)
from ..core.structures import (
    TransactionRequest,
    USCreditApp,
    USJointCreditApp,
    CACreditApp,
    CAJointCreditApp
)

WIDGETS = {
    'main_date_of_birth': DatePickerInput(),
    'joint_date_of_birth': DatePickerInput(),
    'main_photo_id_expiration': DatePickerInput(),
    'joint_photo_id_expiration': DatePickerInput(),
    'main_time_at_address': FuzzyDurationWidget(),
    'main_time_at_employer': FuzzyDurationWidget(),
    'joint_time_at_employer': FuzzyDurationWidget(),
    'insurance': BooleanSelect(),
}


class SubmitTransactionForm(forms.ModelForm):
    class Meta:
        model = TransactionRequest
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].disabled = True
        self.fields['source_account'].disabled = True
        self.fields['dest_account'].disabled = True



class ApplicationSelectionForm(forms.Form):
    region = forms.ChoiceField(label=_("Region"), required=True, choices=REGIONS)
    language = forms.ChoiceField(label=_("Language"), required=True, choices=LANGUAGES)
    app_type = forms.ChoiceField(label=_('Application Type'), required=True, choices=APP_TYPES)

    def clean_language(self):
        region = self.cleaned_data['region']
        language = self.cleaned_data['language']
        locale = LOCALES.get(region, {}).get(language)
        if not locale:
            msg = _('Selected language is not valid for the selected region.')
            raise ValidationError(msg)
        return language


class BaseCreditAppFormMixin(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['region'].disabled = True
        self.fields['language'].disabled = True
        self.fields['app_type'].disabled = True


class USCreditAppForm(BaseCreditAppFormMixin, forms.ModelForm):
    dashboard_template = 'wfrs/dashboard/application_us_single.html'

    class Meta:
        model = USCreditApp
        widgets = WIDGETS
        fields = '__all__'


class USJointCreditAppForm(BaseCreditAppFormMixin, forms.ModelForm):
    dashboard_template = 'wfrs/dashboard/application_us_joint.html'

    class Meta:
        model = USJointCreditApp
        widgets = WIDGETS
        fields = '__all__'


class CACreditAppForm(BaseCreditAppFormMixin, forms.ModelForm):
    dashboard_template = 'wfrs/dashboard/application_ca_single.html'

    class Meta:
        model = CACreditApp
        widgets = WIDGETS
        fields = '__all__'


class CAJointCreditAppForm(BaseCreditAppFormMixin, forms.ModelForm):
    dashboard_template = 'wfrs/dashboard/application_ca_joint.html'

    class Meta:
        model = CAJointCreditApp
        widgets = WIDGETS
        fields = '__all__'


def get_application_form_class(region, app_type):
    classes = {
        US: {
            INDIVIDUAL: USCreditAppForm,
            JOINT: USJointCreditAppForm,
        },
        CA: {
            INDIVIDUAL: CACreditAppForm,
            JOINT: CAJointCreditAppForm,
        },
    }
    return classes.get(region, {}).get(app_type)
