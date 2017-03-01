from django.contrib.auth.models import User, Group
from .base import BaseTest
from ..models import APICredentials


class APICredentialsTest(BaseTest):
    def test_selection_no_user(self):
        APICredentials.objects.create(
            username='credsA',
            password='',
            merchant_num='',
            user_group=None,
            priority=1)
        APICredentials.objects.create(
            username='credsB',
            password='',
            merchant_num='',
            user_group=None,
            priority=2)
        self.assertEqual(APICredentials.get_credentials().username, 'credsB')


    def test_selection_user_no_group(self):
        APICredentials.objects.create(
            username='credsA',
            password='',
            merchant_num='',
            user_group=None,
            priority=1)
        APICredentials.objects.create(
            username='credsB',
            password='',
            merchant_num='',
            user_group=None,
            priority=2)
        user = User.objects.create_user(username='bill')
        self.assertEqual(APICredentials.get_credentials(user).username, 'credsB')

    def test_selection_user_group(self):
        group = Group.objects.create(name='Special Group')
        APICredentials.objects.create(
            username='credsA',
            password='',
            merchant_num='',
            user_group=None,
            priority=1)
        APICredentials.objects.create(
            username='credsB',
            password='',
            merchant_num='',
            user_group=group,
            priority=2)
        user = User.objects.create_user(username='bill')
        self.assertEqual(APICredentials.get_credentials(user).username, 'credsA')
        user.groups.add(group)
        self.assertEqual(APICredentials.get_credentials(user).username, 'credsB')
        user.groups.remove(group)
        self.assertEqual(APICredentials.get_credentials(user).username, 'credsA')
