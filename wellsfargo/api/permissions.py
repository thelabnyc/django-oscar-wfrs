from django.db.models import Q
from rest_framework import permissions
from oscar.core.loading import get_model

Account = get_model('oscar_accounts', 'Account')


class IsAccountOwner(permissions.BasePermission):
    """
    Object-level permission to make sure on the primary_user and
    secondary_users of an account can view or edit it.
    """
    @classmethod
    def list_valid_account_ids(self, request):
        is_primary = Q(primary_user=request.user)
        is_secondary = Q(secondary_users=request.user)
        return Account.objects.filter(is_primary | is_secondary).values_list('id', flat=True)

    def has_object_permission(self, request, view, account):
        valid_account_ids = self.list_valid_account_ids(request)
        return account.id in valid_account_ids
