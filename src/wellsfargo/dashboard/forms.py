from django import forms
from django.utils.translation import gettext_lazy as _
from oscar.forms.widgets import DateTimePickerInput
from ..core.constants import (
    CREDIT_APP_STATUSES,
    PREQUAL_TRANS_STATUS_CHOICES,
)
from ..models import (
    FinancingPlan,
    FinancingPlanBenefit,
)


class FinancingPlanForm(forms.ModelForm):
    class Meta:
        model = FinancingPlan
        fields = (
            'plan_number', 'description', 'fine_print_superscript', 'apr', 'term_months',
            'product_price_threshold', 'advertising_enabled', 'is_default_plan', 'allow_credit_application')


class FinancingPlanBenefitForm(forms.ModelForm):
    class Meta:
        model = FinancingPlanBenefit
        fields = ('group_name', 'plans')


class ApplicationSearchForm(forms.Form):
    # Basic Search
    search_text = forms.CharField(required=False, label="Search")

    # Advanced Search
    status = forms.ChoiceField(required=False, label=_("Status"), choices=((('', _('All Statuses')), ) + CREDIT_APP_STATUSES))
    name = forms.CharField(required=False, label=_("Applicant Name"))
    email = forms.CharField(required=False, label=_("Applicant Email Address"))
    address = forms.CharField(required=False, label=_("Applicant Address"))
    phone = forms.CharField(required=False, label=_("Applicant Phone Number"))
    created_date_from = forms.DateTimeField(required=False, label=_("Submitted After"), widget=DateTimePickerInput)
    created_date_to = forms.DateTimeField(required=False, label=_("Submitted Before"), widget=DateTimePickerInput)
    submitted_by = forms.CharField(required=False, label=_("Submitted By"))

    # Hidden filters linked to by other parts of the application
    user_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    submitting_user_id = forms.IntegerField(required=False, widget=forms.HiddenInput())


class PreQualSearchForm(forms.Form):
    # Basic Search
    search_text = forms.CharField(required=False, label=_("Search"))

    # Advanced Search
    customer_initiated = forms.NullBooleanField(required=False, label=_("Customer Initiated?"))
    first_name = forms.CharField(required=False, label=_("First Name"))
    last_name = forms.CharField(required=False, label=_("Last Name"))
    status = forms.ChoiceField(required=False, label=_("Status"), choices=((('', _('All Statuses')), ) + PREQUAL_TRANS_STATUS_CHOICES))
    created_date_from = forms.DateTimeField(required=False, label=_("Submitted After"), widget=DateTimePickerInput)
    created_date_to = forms.DateTimeField(required=False, label=_("Submitted Before"), widget=DateTimePickerInput)


class SDKApplicationSearchForm(forms.Form):
    # Basic Search
    search_text = forms.CharField(required=False, label=_("Search"))

    # Advanced Search
    created_date_from = forms.DateTimeField(required=False, label=_("Submitted After"), widget=DateTimePickerInput)
    created_date_to = forms.DateTimeField(required=False, label=_("Submitted Before"), widget=DateTimePickerInput)
