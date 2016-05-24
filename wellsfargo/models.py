from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    RegexValidator,
    MinValueValidator,
    MaxValueValidator,
    MinLengthValidator,
    MaxLengthValidator)
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_model
from oscar_accounts.core import redemptions_account
from oscar_accounts import names, facade
from .fields import (
    USSocialSecurityNumberField,
    USStateField,
    USZipCodeField,
    USPhoneNumberField,
    CASocialInsuranceNumberField,
    CAProvinceField,
    CAPostalCodeField,
    CAPhoneNumberField)
from .settings import WFRS_CREDIT_LINE
import logging

AccountType = get_model('oscar_accounts', 'AccountType')
Account = get_model('oscar_accounts', 'Account')
Transfer = get_model('oscar_accounts', 'Transfer')

logger = logging.getLogger(__name__)


CREDIT_APP_APPROVED = 'E0'
CREDIT_APP_DECISION_DELAYED = 'E1'
CREDIT_APP_FORMAT_ERROR = 'E2'
CREDIT_APP_WFF_ERROR = 'E3'
CREDIT_APP_DENIED = 'E4'

TRANS_DECLINED = 'A0'
TRANS_APPROVED = 'A1'
TRANS_VOID_NO_MATCH_FOUND = 'A2'
TRANS_VOID_MATCH_DUPLICATE = 'A3'
TRANS_STATUSES = (
    (TRANS_DECLINED, _("Transaction not approved or declined. For time-out reversal and void transactions, match was found but was already funded.")),
    (TRANS_APPROVED, _("Approved. For time-out reversal and void transactions, match was found and processed.")),
    (TRANS_VOID_NO_MATCH_FOUND, _("Time-out reversal or void approved, but no matching transaction was found.")),
    (TRANS_VOID_MATCH_DUPLICATE, _("Time-out reversal or void approved, but matched duplicate transactions.")),
)

TRANS_TYPE_AUTH = '5'
TRANS_TYPE_CANCEL_AUTH = '7'
# TRANS_TYPE_CHARGE = '3'
# TRANS_TYPE_AUTH_AND_CHARGE = '1'
# TRANS_TYPE_AUTH_AND_CHARGE_TIMEOUT_REVERSAL = '2'
TRANS_TYPE_RETURN_CREDIT = '4'
TRANS_TYPE_RETURN_CREDIT_TIMEOUT_REVERSAL = '9'
TRANS_TYPE_VOID_SALE = 'VS'
TRANS_TYPE_VOID_RETURN = 'VR'
TRANS_TYPE_INQUIRY = '8'
TRANS_TYPE_APPLY = 'A6'
TRANS_TYPES = (
    (TRANS_TYPE_AUTH, _('Authorization for Future Charge')),
    (TRANS_TYPE_CANCEL_AUTH, _('Cancel Existing Authorization')),
    # (TRANS_TYPE_CHARGE, _('Charge for Previous Authorization')), # TODO: handle charges
    # (TRANS_TYPE_AUTH_AND_CHARGE, _('Authorize and Charge')),
    # (TRANS_TYPE_AUTH_AND_CHARGE_TIMEOUT_REVERSAL, _('Time-out Reversal for Previous "Authorization and Charge"')),
    (TRANS_TYPE_RETURN_CREDIT, _('Return or Credit')),
    (TRANS_TYPE_RETURN_CREDIT_TIMEOUT_REVERSAL, _('Time-out Reversal for Return or Credit')),
    (TRANS_TYPE_VOID_SALE, _('Void Sale')),
    (TRANS_TYPE_VOID_RETURN, _('Void Return')),
    # These transaction types are special and are handled separately
    # (TRANS_TYPE_INQUIRY, _('Account Inquiry')),
    # (TRANS_TYPE_APPLY, _('Credit Line Application')),
)


INDIVIDUAL, JOINT = ('I', 'J')
APP_TYPES = (
    (INDIVIDUAL, _('Individual')),
    (JOINT, _('Joint')),
)

ENGLISH, FRENCH = ('E', 'F')
LANGUAGES = (
    (ENGLISH, _('English')),
    (FRENCH, _('French')),
)

US, CA = ('US', 'CA')
REGIONS = (
    (US, _('United States')),
    (CA, _('Canada')),
)

EN_US, EN_CA, FR_CA = ('en_US', 'en_CA', 'fr_CA')
LOCALE_CHOICES = (
    (EN_US, _('English (US)')),
    (EN_CA, _('English (CA)')),
    (FR_CA, _('French (CA)')),
)
LOCALES = {
    US: {
        ENGLISH: EN_US,
    },
    CA: {
        ENGLISH: EN_CA,
        FRENCH: FR_CA,
    },
}

HOUSING_STATUSES = {
    US: (
        ('R', _('Rent')),
        ('O', _('Own')),
        ('OT', _('Other')),
    ),
    CA: (
        ('R', _('Rent')),
        ('O', _('Own')),
    ),
}

PHOTO_ID_TYPES = {
    CA: (
        ('OA', _('Old Age Security Card')),
        ('DL', _('Driver’s License')),
        ('PI', _('Provincial ID')),
        ('PA', _('Canadian Passport')),
        ('CN', _('Certificate of Citizenship or Naturalization')),
        ('IS', _('Certificate of Indian Status')),
        ('CC', _('Canadian Citizen Form 1000 or 1442')),
    ),
}



class AccountMetadata(models.Model):
    account = models.OneToOneField(Account,
        verbose_name=_("Account"),
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='wfrs_metadata')
    locale = models.CharField(_('Locale'), choices=LOCALE_CHOICES, max_length=5)
    account_number = models.CharField(_("Wells Fargo Account Number"), max_length=16, validators=[
        MinLengthValidator(16),
        MinLengthValidator(16),
    ])



class TransferMetadata(models.Model):
    transfer = models.OneToOneField(Transfer,
        verbose_name=_("Transfer"),
        on_delete=models.CASCADE,
        related_name='wfrs_metadata')
    type_code = models.CharField(_("Transaction Type"), choices=TRANS_TYPES, max_length=2)

    ticket_number = models.CharField(_("Ticket Number"), null=True, blank=True, max_length=12)
    plan_number = models.CharField(_("Plan Number"), max_length=4, validators=[
        MinLengthValidator(4),
        MinValueValidator(1001),
        MaxValueValidator(9999),
    ])

    auth_number = models.CharField(_("Authorization Number"), null=True, blank=True, max_length=6, default='000000')
    status = models.CharField(_("Status"), choices=TRANS_STATUSES, max_length=2)
    message = models.TextField(_("Message"))
    disclosure = models.TextField(_("Disclosure"))

    @classmethod
    def build_auth_request(cls, plan_number, ticket_number, amount):
        request = cls()
        request.plan_number = plan_number
        request.ticket_number = ticket_number
        request.amount = amount
        return request

    @property
    def type_name(self):
        return dict(TRANS_TYPES).get(self.type_code)

    @property
    def status_name(self):
        return dict(TRANS_STATUSES).get(self.status)



# |============================================================== |
# | Credit applications are Django models, but they are *never*   |
# | persisted to the DB since it's unnecessary. We only need the  |
# | data long enough to submit it to Wells. We only use model     |
# | objects to that validating forms and serializers are easier   |
# | to build.                                                     |
# |============================================================== ↓


class TransactionRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True,
        verbose_name=_("Requesting User"),
        related_name='transaction_requests',
        on_delete=models.CASCADE)
    type_code = models.CharField(_("Transaction Type"), choices=TRANS_TYPES, default=TRANS_TYPE_AUTH, max_length=2)
    source_account = models.ForeignKey(Account,
        verbose_name=_("Source Account"),
        related_name='source_requests',
        on_delete=models.CASCADE)
    dest_account = models.ForeignKey(Account,
        verbose_name=_("Destination Account"),
        related_name='dest_requests',
        on_delete=models.CASCADE)
    ticket_number = models.CharField(_("Ticket Number"), null=True, blank=True, max_length=12)
    plan_number = models.CharField(_("Plan Number"), max_length=4, validators=[
        MinLengthValidator(4),
    ])
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    auth_number = models.CharField(_("Authorization Number"), max_length=6, default='000000', validators=[
        MinLengthValidator(6),
        MinLengthValidator(6),
        RegexValidator(r'^[0-9]{6}$'),
    ])

    @classmethod
    def build_auth_request(cls, source_account, plan_number, amount, dest_account=None, ticket_number=None, user=None):
        if not dest_account:
            dest_account = redemptions_account()
        request = cls()
        request.user = user
        request.type_code = TRANS_TYPE_AUTH
        request.source_account = source_account
        request.dest_account = dest_account
        request.plan_number = plan_number
        request.amount = amount
        request.auth_number = '000000'
        request.ticket_number = ticket_number
        return request

    def save(self):
        raise RuntimeError('Can not save TransactionRequest. Object must be transient only.')



class BaseCreditAppMixin(models.Model):
    region = models.CharField(_("Region"), null=False, blank=False, choices=REGIONS, max_length=15)
    language = models.CharField(_("Language"), null=False, blank=False, choices=LANGUAGES, max_length=1)
    app_type = models.CharField(_('Application Type'), null=False, blank=False, choices=APP_TYPES, max_length=1)

    purchase_price = models.IntegerField(_("Requested Credit Amount"), null=True, blank=True)

    main_first_name = models.CharField(_("First Name"), null=False, blank=False, max_length=15)
    main_last_name = models.CharField(_("Last Name"), null=False, blank=False, max_length=20)
    main_middle_initial = models.CharField(_("Middle Initial"), null=True, blank=True, max_length=1)
    main_date_of_birth = models.DateField(_("Date of Birth"), null=False, blank=False)
    main_address_line1 = models.CharField(_("Address Line 1"), null=False, blank=False, max_length=35)
    main_address_line2 = models.CharField(_("Address Line 2"), null=True, blank=True, max_length=35)
    main_address_city = models.CharField(_("City"), null=False, blank=False, max_length=15)
    main_home_value = models.IntegerField(_("Home Value"), null=True, blank=True)
    main_mortgage_balance = models.IntegerField(_("Mortgage Balance"), null=True, blank=True)
    main_annual_income = models.IntegerField(_("Annual Income"), null=False, blank=False)

    insurance = models.BooleanField(_('Optional Insurance'), null=False)
    sales_person_id = models.CharField(_("Existing Sales Person ID"), null=True, blank=True, max_length=4, validators=[
        MinLengthValidator(4),
        MaxLengthValidator(4),
    ])
    new_sales_person = models.CharField(_("New Sales Person Name"), null=True, blank=True, max_length=10)
    email = models.EmailField(_("Email"), null=False, blank=False, max_length=80)

    class Meta:
        abstract = True

    @property
    def locale(self):
        return LOCALES.get(self.region, {}).get(self.language)

    @property
    def is_joint(self):
        return False

    @property
    def full_name(self):
        return "%s %s" % (self.main_first_name, self.main_last_name)


    def save(self):
        raise RuntimeError('Can not save credit application. Object must be transient only.')


class BaseJointCreditAppMixin(BaseCreditAppMixin):
    joint_first_name = models.CharField(_("First Name"), null=False, blank=False, max_length=15)
    joint_last_name = models.CharField(_("Last Name"), null=False, blank=False, max_length=20)
    joint_middle_initial = models.CharField(_("Middle Initial"), null=True, blank=True, max_length=1)
    joint_date_of_birth = models.DateField(_("Date of Birth"), null=False, blank=False)
    joint_address_line1 = models.CharField(_("Address Line 1"), null=False, blank=False, max_length=35)
    joint_address_line2 = models.CharField(_("Address Line 2"), null=True, blank=True, max_length=35)
    joint_address_city = models.CharField(_("City"), null=False, blank=False, max_length=15)
    joint_annual_income = models.IntegerField(_("Annual Income"), null=False, blank=False)

    class Meta:
        abstract = True

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

    def clean(self):
        self._clean_dl_province('joint_drivers_license_province', self.joint_photo_id_type, self.joint_drivers_license_province)



class USCreditApp(USCreditAppMixin, BaseCreditAppMixin):
    pass


class USJointCreditApp(USJointCreditAppMixin, BaseJointCreditAppMixin):
    pass


class CACreditApp(CACreditAppMixin, BaseCreditAppMixin):
    pass


class CAJointCreditApp(CAJointCreditAppMixin, BaseJointCreditAppMixin):
    pass



# |====================================================== |
# | Transient structures that aren't really models at all |
# |====================================================== ↓


class AccountInquiryResult(object):
    account = None
    balance = Decimal('0.00')
    open_to_buy = Decimal('0.00')

    @transaction.atomic()
    def reconcile(self, user=None):
        # Perform a transfer to make the account balance match WF. This will overtime
        # mirror customer payments into Wells Fargo (that we don't have notifications of)
        balance_wf = -(self.balance)
        balance_us = self.account.balance
        balance_change = balance_wf - balance_us
        if balance_change != Decimal('0.00'):
            logger.info('Reconciling balance offset of %s on account %s' % (balance_change, self.account))
            transfer = facade.transfer(
                description=_('Automatic compensating transaction during reconciliation with Wells Fargo Retail Services.'),
                source=Account.objects.get(name=names.BANK),
                destination=self.account,
                amount=balance_change,
                user=user)
        else:
            logger.info('Reconciliation not needed. Recorded balance matches WFRS records for account %s' % (self.account))

        assert self.account.balance == balance_wf

        # Adjust the credit limit to match WF. Should be equal to the sum of `balance` and `open_to_buy`
        self.account.credit_limit = (self.balance + self.open_to_buy)
        self.account.save()



class CreditApplicationResult(object):
    application = None
    transaction_status = ""
    account_number = ""
    credit_limit = Decimal('0.00')
    owner = None

    @property
    def is_approved(self):
        return (self.transaction_status == CREDIT_APP_APPROVED)

    @transaction.atomic()
    def save(self):
        if not self.is_approved:
            return None

        try:
            wfrs = AccountType.objects.get(name=WFRS_CREDIT_LINE)
        except AccountType.DoesNotExist:
            wfrs = AccountType.add_root(name=WFRS_CREDIT_LINE)
            wfrs.save()

        try:
            account = Account.objects.get(account_type=wfrs, code=self.account_number)
        except Account.DoesNotExist:
            account = Account()
            account.account_type = wfrs
            account.code = self.account_number

        if self.application:
            account.name = '%s – %s' % (self.application.full_name, self.account_number)

        account.primary_user = self.owner
        account.status = Account.OPEN
        account.credit_limit = self.credit_limit
        account.save()

        meta, created = AccountMetadata.objects.get_or_create(account=account)
        meta.locale = self.application.locale
        meta.account_number = self.account_number
        meta.save()

        return account
