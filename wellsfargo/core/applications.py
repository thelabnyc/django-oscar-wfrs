from django.core.exceptions import ValidationError
from django.core.validators import (
    RegexValidator,
    MinLengthValidator,
    MaxLengthValidator,
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_model
from .constants import (
    US, CA,
    ENGLISH,
    INDIVIDUAL,
    APP_TYPES,
    HOUSING_STATUSES,
    LANGUAGES,
    LOCALES,
    PHOTO_ID_TYPES,
    REGIONS,
)
from .fields import (
    USSocialSecurityNumberField,
    USStateField,
    USZipCodeField,
    USPhoneNumberField,
    CASocialInsuranceNumberField,
    DateOfBirthField,
    CAProvinceField,
    CAPostalCodeField,
    CAPhoneNumberField
)

Account = get_model('oscar_accounts', 'Account')


class BaseCreditAppMixin(models.Model):
    region = models.CharField(_("Region"), null=False, blank=False, choices=REGIONS, max_length=15, default=US)
    language = models.CharField(_("Language"), null=False, blank=False, choices=LANGUAGES, max_length=1, default=ENGLISH)
    app_type = models.CharField(_('Application Type'), null=False, blank=False, choices=APP_TYPES, max_length=1, default=INDIVIDUAL)

    purchase_price = models.IntegerField(_("Requested Credit Amount"), null=True, blank=True, validators=[
        MinValueValidator(0),
        MaxValueValidator(99999),
    ])

    main_first_name = models.CharField(_("First Name"), null=False, blank=False, max_length=15)
    main_last_name = models.CharField(_("Last Name"), null=False, blank=False, max_length=20)
    main_middle_initial = models.CharField(_("Middle Initial"), null=True, blank=True, max_length=1)
    main_date_of_birth = DateOfBirthField(_("Date of Birth"), blank=False)
    main_address_line1 = models.CharField(_("Address Line 1"), null=False, blank=False, max_length=35)
    main_address_line2 = models.CharField(_("Address Line 2"), null=True, blank=True, max_length=35)
    main_address_city = models.CharField(_("City"), null=False, blank=False, max_length=15)
    main_home_value = models.IntegerField(_("Home Value"), null=True, blank=True, validators=[
        MinValueValidator(0),
        MaxValueValidator(9999999),
    ])
    main_mortgage_balance = models.IntegerField(_("Mortgage Balance"), null=True, blank=True, validators=[
        MinValueValidator(0),
        MaxValueValidator(9999999),
    ])
    main_annual_income = models.IntegerField(_("Annual Income"), null=False, blank=False, validators=[
        MinValueValidator(0),
        MaxValueValidator(999999),
    ])

    insurance = models.BooleanField(_('Optional Insurance'), null=False, default=False)
    sales_person_id = models.CharField(_("Existing Sales Person ID"), null=True, blank=True, max_length=4, validators=[
        MinLengthValidator(4),
        MaxLengthValidator(4),
    ])
    new_sales_person = models.CharField(_("New Sales Person Name"), null=True, blank=True, max_length=10)
    email = models.EmailField(_("Email"), null=False, blank=False, max_length=80)

    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        verbose_name = "Credit Application"
        verbose_name_plural = "Credit Applications"
        ordering = ('-created_datetime', )

    @property
    def locale(self):
        return LOCALES.get(self.region, {}).get(self.language)

    @property
    def is_joint(self):
        return False

    @property
    def full_name(self):
        return "%s %s" % (self.main_first_name, self.main_last_name)


class BaseJointCreditAppMixin(BaseCreditAppMixin):
    joint_first_name = models.CharField(_("First Name"), null=False, blank=False, max_length=15)
    joint_last_name = models.CharField(_("Last Name"), null=False, blank=False, max_length=20)
    joint_middle_initial = models.CharField(_("Middle Initial"), null=True, blank=True, max_length=1)
    joint_date_of_birth = DateOfBirthField(_("Date of Birth"), blank=False)
    joint_address_line1 = models.CharField(_("Address Line 1"), null=False, blank=False, max_length=35)
    joint_address_line2 = models.CharField(_("Address Line 2"), null=True, blank=True, max_length=35)
    joint_address_city = models.CharField(_("City"), null=False, blank=False, max_length=15)
    joint_annual_income = models.IntegerField(_("Annual Income"), null=False, blank=False, validators=[
        MinValueValidator(0),
        MaxValueValidator(999999),
    ])

    class Meta:
        abstract = True
        verbose_name = "Joint Credit Application"
        verbose_name_plural = "Joint Credit Applications"

    @property
    def is_joint(self):
        return True


class USCreditAppMixin(models.Model):
    main_ssn = USSocialSecurityNumberField(_("Social Security Number"), null=False, blank=False)
    main_address_state = USStateField(_("State"), null=False, blank=False)
    main_address_postcode = USZipCodeField(_("Postcode"), null=False, blank=False)
    main_home_phone = USPhoneNumberField(_("Home Phone"), null=False, blank=False)
    main_time_at_address = models.CharField(_("Time at Address"), null=True, blank=True, max_length=4, validators=[
        MinLengthValidator(4),
        MaxLengthValidator(4),
        RegexValidator(r'^[0-9]{4}$'),
    ])
    main_housing_status = models.CharField(_("Housing Status"), null=True, blank=True, choices=HOUSING_STATUSES[US], max_length=3)
    main_employer_name = models.CharField(_("Employer Name"), null=True, blank=True, max_length=30)
    main_time_at_employer = models.CharField(_("Time at Employer"), null=True, blank=True, max_length=4, validators=[
        MinLengthValidator(4),
        MaxLengthValidator(4),
        RegexValidator(r'^[0-9]{4}$'),
    ])
    main_employer_phone = USPhoneNumberField(_("Employer Phone Number"), null=False, blank=False)
    main_cell_phone = USPhoneNumberField(_("Cell Phone"), null=True, blank=True)
    main_occupation = models.CharField(_("Occupation"), null=True, blank=True, max_length=24)

    class Meta:
        abstract = True
        verbose_name = "US Individual Credit Application"
        verbose_name_plural = "US Individual Credit Applications"


class USJointCreditAppMixin(USCreditAppMixin):
    joint_ssn = USSocialSecurityNumberField(_("Social Security Number"), null=False, blank=False)
    joint_address_state = USStateField(_("State"), null=False, blank=False)
    joint_address_postcode = USZipCodeField(_("Postcode"), null=False, blank=False)
    joint_employer_name = models.CharField(_("Employer Name"), null=True, blank=True, max_length=30)
    joint_time_at_employer = models.CharField(_("Time at Employer"), null=True, blank=True, max_length=4, validators=[
        MinLengthValidator(4),
        MaxLengthValidator(4),
        RegexValidator(r'^[0-9]{4}$'),
    ])
    joint_employer_phone = USPhoneNumberField(_("Employer Phone Number"), null=False, blank=False)
    joint_cell_phone = USPhoneNumberField(_("Cell Phone"), null=True, blank=True)
    joint_occupation = models.CharField(_("Occupation"), null=True, blank=True, max_length=24)

    class Meta:
        abstract = True
        verbose_name = "US Joint Credit Application"
        verbose_name_plural = "US Joint Credit Applications"


class CACreditAppMixin(models.Model):
    main_ssn = CASocialInsuranceNumberField(_("Social Insurance Number"), null=True, blank=True)
    main_address_state = CAProvinceField(_("Province"), null=False, blank=False)
    main_address_postcode = CAPostalCodeField(_("Postcode"), null=False, blank=False)
    main_home_phone = CAPhoneNumberField(_("Home Phone"), null=False, blank=False)
    main_time_at_address = models.CharField(_("Time at Address"), null=False, blank=False, max_length=4, validators=[
        MinLengthValidator(4),
        MaxLengthValidator(4),
        RegexValidator(r'^[0-9]{4}$'),
    ])
    main_housing_status = models.CharField(_("Housing Status"), null=False, blank=False, choices=HOUSING_STATUSES[CA], max_length=3)
    main_employer_name = models.CharField(_("Employer Name"), null=False, blank=False, max_length=30)
    main_time_at_employer = models.CharField(_("Time at Employer"), null=False, blank=False, max_length=4, validators=[
        MinLengthValidator(4),
        MaxLengthValidator(4),
        RegexValidator(r'^[0-9]{4}$'),
    ])
    main_employer_phone = CAPhoneNumberField(_("Employer Phone Number"), null=False, blank=False)
    main_cell_phone = CAPhoneNumberField(_("Cell Phone"), null=True, blank=True)
    main_occupation = models.CharField(_("Occupation"), null=False, blank=False, max_length=24)
    main_photo_id_type = models.CharField(_("Photo ID Type"), null=False, blank=False, choices=PHOTO_ID_TYPES[CA], max_length=2)
    main_photo_id_number = models.CharField(_("Photo ID Number"), null=False, blank=False, max_length=4, validators=[
        MinLengthValidator(4),
        MaxLengthValidator(4),
    ])
    main_drivers_license_province = CAProvinceField(_("Driver’s License Province"), null=True, blank=True)
    main_photo_id_expiration = models.DateField(_("Photo ID Expiration Date"), null=False, blank=False)

    class Meta:
        abstract = True
        verbose_name = "CA Individual Credit Application"
        verbose_name_plural = "CA Individual Credit Applications"

    def clean(self):
        self._clean_dl_province('main_drivers_license_province', self.main_photo_id_type, self.main_drivers_license_province)

    def _clean_dl_province(self, name, photo_id_type, drivers_license_province):
        if photo_id_type == 'DL' and drivers_license_province is None:
            err = ValidationError(_('"Driver’s License Province" is required if Photo ID Type is "Driver’s License"'))
            raise ValidationError({ name: err.error_list })



class CAJointCreditAppMixin(CACreditAppMixin):
    joint_ssn = CASocialInsuranceNumberField(_("Social Insurance Number"), null=True, blank=True)
    joint_address_state = CAProvinceField(_("Province"), null=False, blank=False)
    joint_address_postcode = CAPostalCodeField(_("Postcode"), null=False, blank=False)
    joint_employer_name = models.CharField(_("Employer Name"), null=False, blank=False, max_length=30)
    joint_time_at_employer = models.CharField(_("Time at Employer"), null=False, blank=False, max_length=4, validators=[
        MinLengthValidator(4),
        MaxLengthValidator(4),
        RegexValidator(r'^[0-9]{4}$'),
    ])
    joint_employer_phone = CAPhoneNumberField(_("Employer Phone Number"), null=False, blank=False)
    joint_cell_phone = CAPhoneNumberField(_("Cell Phone"), null=True, blank=True)
    joint_occupation = models.CharField(_("Occupation"), null=False, blank=False, max_length=24)
    joint_photo_id_type = models.CharField(_("Photo ID Type"), null=False, blank=False, choices=PHOTO_ID_TYPES[CA], max_length=3)
    joint_photo_id_number = models.CharField(_("Photo ID Number"), null=False, blank=False, max_length=4, validators=[
        MinLengthValidator(4),
        MaxLengthValidator(4),
    ])
    joint_drivers_license_province = CAProvinceField(_("Driver’s License Province"), null=True, blank=True)
    joint_photo_id_expiration = models.DateField(_("Photo ID Expiration Date"), null=False, blank=False)

    class Meta:
        abstract = True
        verbose_name = "CA Joint Credit Application"
        verbose_name_plural = "CA Joint Credit Applications"

    def clean(self):
        self._clean_dl_province('joint_drivers_license_province', self.joint_photo_id_type, self.joint_drivers_license_province)
