from django.db.models import CharField, DateField
from django.utils.translation import ugettext_lazy as _
from localflavor.us.forms import USSocialSecurityNumberField as StockUSSocialSecurityNumberFormField
from localflavor.us.models import (
    USSocialSecurityNumberField as StockUSSocialSecurityNumberField,
    USStateField,
    USZipCodeField,
)
from localflavor.ca.ca_provinces import PROVINCE_CHOICES
from localflavor.ca.forms import (
    CASocialInsuranceNumberField as CASocialInsuranceNumberFieldFormField,
    CAProvinceField as CAProvinceFieldFormField,
    CAPostalCodeField as CAPostalCodeFieldFormField,
)
import re


class SocialInsuranceFormField(CASocialInsuranceNumberFieldFormField):
    def __init__(self, max_length=None, empty_value=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class USSocialSecurityNumberFormField(StockUSSocialSecurityNumberFormField):
    def clean(self, value):
        # These values are normally blocked by SSN validation, however we need them to be
        # allowed since the WFRS API uses them for selecting test responses. In production
        # their API will flag them as invalid.
        test_values = ('999999990', '999999991', '999999992', '999999993', '999999994')
        ssn = re.sub('[^0-9]', '', value)
        if ssn in test_values:
            return value
        return super().clean(value)


class USSocialSecurityNumberField(StockUSSocialSecurityNumberField):
    """
    Model field for collecting a US SSN. Collects a full SSN, but only persists a
    masked version of the actual data.
    """
    def formfield(self, **kwargs):
        defaults = {'form_class': USSocialSecurityNumberFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def pre_save(self, model_instance, add):
        full_ssn = getattr(model_instance, self.attname)
        masked_ssn = 'xxx-xx-%s' % full_ssn[-4:]
        return masked_ssn


class CASocialInsuranceNumberField(CharField):
    """
    Model field for collecting a CA Social Insurance Number. Collects a full SIN, but only
    persists a masked version of the actual data.
    """
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

    def pre_save(self, model_instance, add):
        full_sin = getattr(model_instance, self.attname)
        masked_sin = 'xxx-xxx-%s' % full_sin[-3:]
        return masked_sin


class DateOfBirthField(DateField):
    """
    Model field for collecting date of birth. Collects a valid date, but always stores
    null in the DB.
    """
    def __init__(self, verbose_name=None, name=None, **kwargs):
        kwargs['null'] = True
        super().__init__(verbose_name, name, **kwargs)

    def pre_save(self, model_instance, add):
        return None


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


__all__ = [
    'USSocialSecurityNumberField',
    'USStateField',
    'USZipCodeField',
    'CASocialInsuranceNumberField',
    'CAProvinceField',
    'CAPostalCodeField',
]
