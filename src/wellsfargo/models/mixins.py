from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.models.fields import NullCharField
from ..security import encrypt_account_number, decrypt_account_number



class AccountNumberMethodsMixin(models.Model):
    class Meta:
        abstract = True

    @property
    def masked_account_number(self):
        return 'xxxxxxxxxxxx{}'.format(self.last4_account_number or 'xxxx')

    @property
    def account_number(self):
        acct_num = None
        if self.encrypted_account_number:
            acct_num = decrypt_account_number(self.encrypted_account_number)
        if not acct_num:
            acct_num = self.masked_account_number
        return acct_num

    @account_number.setter
    def account_number(self, value):
        if len(value) != 16:
            raise ValueError(_('Account number must be 16 digits long'))
        self.last4_account_number = value[-4:]
        self.encrypted_account_number = encrypt_account_number(value)

    def purge_encrypted_account_number(self):
        self.encrypted_account_number = None
        self.save()



class AccountNumberMixin(AccountNumberMethodsMixin, models.Model):
    last4_account_number = models.CharField(_("Last 4 digits of account number"), max_length=4)
    encrypted_account_number = models.BinaryField(null=True)

    class Meta:
        abstract = True



class MaybeAccountNumberMixin(AccountNumberMethodsMixin, models.Model):
    last4_account_number = NullCharField(_("Last 4 digits of account number"), max_length=4)
    encrypted_account_number = models.BinaryField(null=True)

    class Meta:
        abstract = True
