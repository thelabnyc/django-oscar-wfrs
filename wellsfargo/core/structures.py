from decimal import Decimal
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from oscar.core.loading import get_model
from oscar_accounts import names, facade
import logging
from .constants import CREDIT_APP_APPROVED
from ..models import AccountMetadata
from ..settings import WFRS_ACCOUNT_TYPE

AccountType = get_model('oscar_accounts', 'AccountType')
Account = get_model('oscar_accounts', 'Account')

logger = logging.getLogger(__name__)


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
    def save(self, owner=None, status=Account.OPEN, name=None, locale=None):
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

        if name:
            account.name = name
        elif self.application:
            account.name = '%s – %s' % (self.application.full_name, self.account_number)

        # Save account
        account.primary_user = owner or self.application.user
        account.status = status
        account.credit_limit = self.credit_limit
        account.save()

        # Save WFRS account metadata
        meta, created = AccountMetadata.objects.get_or_create(account=account)
        if locale:
            meta.locale = locale
        elif self.application:
            meta.locale = self.application.locale
        meta.account_number = self.account_number
        meta.save()

        # Link application to newly created account
        if self.application:
            self.application.__class__.objects.filter(account=account).update(account=None)
            self.application.account = account
            self.application.save()

        return account
