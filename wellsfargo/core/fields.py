from django.db.models import CharField
from django.utils.translation import ugettext_lazy as _
from localflavor.us.forms import USSocialSecurityNumberField as StockUSSocialSecurityNumberFormField
from localflavor.us.models import (
    USSocialSecurityNumberField as StockUSSocialSecurityNumberField,
    USStateField,
    USZipCodeField,
    PhoneNumberField as USPhoneNumberField
)
from localflavor.ca.ca_provinces import PROVINCE_CHOICES
from localflavor.ca.forms import (
    CASocialInsuranceNumberField as CASocialInsuranceNumberFieldFormField,
    CAProvinceField as CAProvinceFieldFormField,
    CAPostalCodeField as CAPostalCodeFieldFormField,
    CAPhoneNumberField as CAPhoneNumberFieldFormField
)


class SocialInsuranceFormField(CASocialInsuranceNumberFieldFormField):
    def __init__(self, max_length=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PhoneNumberFormField(CAPhoneNumberFieldFormField):
    def __init__(self, max_length=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class USSocialSecurityNumberFormField(StockUSSocialSecurityNumberFormField):
    def clean(self, value):
        # These values are normally blocked by SSN validation, however we need them to be
        # allowed since the WFRS API uses them for selecting test responses. In production
        # their API will flag them as invalid.
        test_values = ('999999990', '999999991', '999999992', '999999993', '999999994')
        if value in test_values:
            return value
        return super().clean(value)


class USSocialSecurityNumberField(StockUSSocialSecurityNumberField):
    def formfield(self, **kwargs):
        defaults = {'form_class': USSocialSecurityNumberFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class CASocialInsuranceNumberField(CharField):
    description = _("Social Insurance number")

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 11
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['max_length']
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = {'form_class': SocialInsuranceFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class CAProvinceField(CharField):
    description = _("Canadian province")

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = PROVINCE_CHOICES
        kwargs['max_length'] = 2
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['choices']
        del kwargs['max_length']
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = {'form_class': CAProvinceFieldFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class CAPostalCodeField(CharField):
    description = _("Canadian postal code")

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 7
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['max_length']
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = {'form_class': CAPostalCodeFieldFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class CAPhoneNumberField(CharField):
    description = _("Phone number")

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 20
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['max_length']
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = {'form_class': PhoneNumberFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)


__all__ = [
    'USSocialSecurityNumberField',
    'USStateField',
    'USZipCodeField',
    'USPhoneNumberField',
    'CASocialInsuranceNumberField',
    'CAProvinceField',
    'CAPostalCodeField',
    'CAPhoneNumberField'
]
