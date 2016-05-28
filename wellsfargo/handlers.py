from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import SuspiciousOperation
from django.dispatch import receiver
from oscar.core.loading import get_model

from .api.permissions import list_session_accounts

Account = get_model('oscar_accounts', 'Account')


@receiver(user_logged_in)
def merge_account_numbers(sender, request, user, **kwargs):
    """Upon login, merge session account numbers into the DB"""
    account_ids = list_session_accounts(request)
    for account in Account.objects.filter(id__in=account_ids).all():
        if account.primary_user and account.primary_user.id != user.id:
            msg = (
                "User %s is attempting to take over Account %s which"
                " is already owned by User %s" % (user, account, account.primary_user)
            )
            raise SuspiciousOperation(msg)
        account.primary_user = user
        account.save()
