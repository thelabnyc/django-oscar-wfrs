from django.db.models import DateField
from localflavor.us.forms import USSocialSecurityNumberField as StockUSSocialSecurityNumberFormField
from localflavor.us.models import (
    USSocialSecurityNumberField as StockUSSocialSecurityNumberField,
    USStateField,
    USZipCodeField,
)
import re


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
        if full_ssn is None:
            return 'xxx-xx-xxxx'
        masked_ssn = 'xxx-xx-%s' % full_ssn[-4:]
        return masked_ssn


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


__all__ = [
    'USSocialSecurityNumberField',
    'USStateField',
    'USZipCodeField',
]
