from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms.models import fields_for_model
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_model
from oscar.forms.widgets import DatePickerInput
from .widgets import FuzzyDurationWidget, BooleanSelect, TypeAheadModelSelect
from ..core.constants import (
    US, CA,
    INDIVIDUAL, JOINT,
    LOCALES,
    APP_TYPES, LANGUAGES, REGIONS
)
from ..models import (
    AccountMetadata,
    FinancingPlan,
    FinancingPlanBenefit,
    TransactionRequest,
    USCreditApp,
    USJointCreditApp,
    CACreditApp,
    CAJointCreditApp
)

Account = get_model('oscar_accounts', 'Account')
BillingAddress = get_model('order', 'BillingAddress')

WIDGETS = {
    'user': TypeAheadModelSelect(view='wfrs-api-user-autocomplete', model=User, attrs={
        'placeholder': _('Start typing to search for a user')
    }),
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
        exclude = ('transfer', )

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


class ManualAddAccountForm(forms.Form):
    _account_fields = fields_for_model(Account, fields=[
        'name', 'primary_user', 'status', 'credit_limit'])
    _meta_fields = fields_for_model(AccountMetadata, fields=[
        'account_number', 'locale'])
    _address_fields = fields_for_model(BillingAddress, fields=[
        'title', 'first_name', 'last_name', 'line1', 'line2', 'line3', 'line4', 'state', 'postcode', 'country'])

    name = _account_fields['name']
    primary_user = _account_fields['primary_user']
    status = forms.ChoiceField(choices=(
        (Account.OPEN, Account.OPEN),
        (Account.FROZEN, Account.FROZEN),
        (Account.CLOSED, Account.CLOSED),
    ))
    credit_limit = _account_fields['credit_limit']

    account_number = _meta_fields['account_number']
    locale = _meta_fields['locale']

    title = _address_fields['title']
    first_name = _address_fields['first_name']
    last_name = _address_fields['last_name']
    line1 = _address_fields['line1']
    line2 = _address_fields['line2']
    line3 = _address_fields['line3']
    line4 = _address_fields['line4']
    state = _address_fields['state']
    postcode = _address_fields['postcode']
    country = _address_fields['country']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = (
            'name', 'primary_user', 'status', 'credit_limit', 'account_number', 'locale',
            'first_name', 'last_name', 'line1', 'line4', 'state', 'postcode', 'country',
        )
        for name in required_fields:
            self.fields[name].required = True
        self.fields['primary_user'].widget = TypeAheadModelSelect(view='wfrs-api-user-autocomplete', model=User, attrs={
            'placeholder': _('Start typing to search for a user')
        })


class FinancingPlanForm(forms.ModelForm):
    class Meta:
        model = FinancingPlan
        fields = ('plan_number', 'description', 'apr', 'term_months', 'is_default_plan')


class FinancingPlanBenefitForm(forms.ModelForm):
    CPATH = '%s.%s' % (FinancingPlanBenefit.__module__, FinancingPlanBenefit.__name__)
    proxy_class = forms.ChoiceField(
        choices=(
            (CPATH, _('Wells Fargo Financing Plan Group')),
        ),
        disabled=True,
        initial=CPATH,
        label=_('Benefit Type'))

    class Meta:
        model = FinancingPlanBenefit
        fields = ('proxy_class', 'group_name', 'plans')


class ApplicationSearchForm(forms.Form):
    app_type = forms.ChoiceField(required=False, label="Application Type", choices=(
        (USCreditApp.APP_TYPE_CODE, _('United States Individual Applications')),
        (USJointCreditApp.APP_TYPE_CODE, _('United States Joint Applications')),
        (CACreditApp.APP_TYPE_CODE, _('Canada Individual Applications')),
        (CAJointCreditApp.APP_TYPE_CODE, _('Canada Joint Applications')),
    ))


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
