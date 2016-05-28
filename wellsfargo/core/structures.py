from decimal import Decimal
from django.conf import settings
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_model
from oscar_accounts import names, facade
from oscar_accounts.core import redemptions_account
import logging

from .applications import (
    USCreditAppMixin,
    BaseCreditAppMixin,
    USJointCreditAppMixin,
    BaseJointCreditAppMixin,
    CACreditAppMixin,
    CAJointCreditAppMixin
)
from .constants import TRANS_TYPES, TRANS_TYPE_AUTH, CREDIT_APP_APPROVED
from .mixins import UnsavableModel

from ..models import AccountMetadata
from ..settings import WFRS_ACCOUNT_TYPE

AccountType = get_model('oscar_accounts', 'AccountType')
Account = get_model('oscar_accounts', 'Account')

logger = logging.getLogger(__name__)


# |==============================================================|
# | Request objects for connector.actions                        |
# |==============================================================|

class TransactionRequest(UnsavableModel, models.Model):
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


class USCreditApp(UnsavableModel, USCreditAppMixin, BaseCreditAppMixin):
    pass


class USJointCreditApp(UnsavableModel, USJointCreditAppMixin, BaseJointCreditAppMixin):
    pass


class CACreditApp(UnsavableModel, CACreditAppMixin, BaseCreditAppMixin):
    pass


class CAJointCreditApp(UnsavableModel, CAJointCreditAppMixin, BaseJointCreditAppMixin):
    pass


# |==============================================================|
# | Response objects for connector.actions                       |
# |==============================================================|

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
            facade.transfer(
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

    @property
    def is_approved(self):
        return (self.transaction_status == CREDIT_APP_APPROVED)

    @transaction.atomic()
    def save(self, owner=None):
        if not self.is_approved:
            return None

        try:
            wfrs = AccountType.objects.get(name=WFRS_ACCOUNT_TYPE)
        except AccountType.DoesNotExist:
            wfrs = AccountType.add_root(name=WFRS_ACCOUNT_TYPE)
            wfrs.save()

        try:
            account = Account.objects.get(account_type=wfrs, code=self.account_number)
        except Account.DoesNotExist:
            account = Account()
            account.account_type = wfrs
            account.code = self.account_number

        if self.application:
            account.name = '%s – %s' % (self.application.full_name, self.account_number)

        account.primary_user = owner
        account.status = Account.OPEN
        account.credit_limit = self.credit_limit
        account.save()

        meta, created = AccountMetadata.objects.get_or_create(account=account)
        meta.locale = self.application.locale
        meta.account_number = self.account_number
        meta.save()

        return account
