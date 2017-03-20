from decimal import Decimal
from django.contrib.auth.models import Group
from wellsfargo.tests.base import BaseTest
from wellsfargo.core.constants import TRANS_TYPE_AUTH, TRANS_APPROVED
from wellsfargo.models import APICredentials, TransferMetadata
import uuid


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
        self.assertEqual(APICredentials.get_credentials(self.joe).username, 'credsB')

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
        self.assertEqual(APICredentials.get_credentials(self.joe).username, 'credsA')
        self.joe.groups.add(group)
        self.assertEqual(APICredentials.get_credentials(self.joe).username, 'credsB')
        self.joe.groups.remove(group)
        self.assertEqual(APICredentials.get_credentials(self.joe).username, 'credsA')



class TransferMetadataTest(BaseTest):

    def test_account_number(self):
        transfer = TransferMetadata()
        transfer.user = self.joe
        transfer.credentials = self.credentials
        transfer.merchant_reference = uuid.uuid1()
        transfer.amount = Decimal('10.00')
        transfer.type_code = TRANS_TYPE_AUTH
        transfer.ticket_number = '123'
        transfer.status = TRANS_APPROVED
        transfer.message = 'message'
        transfer.disclosure = 'disclosure'
        transfer.save()

        # No account number is set
        transfer = TransferMetadata.objects.get(pk=transfer.pk)
        self.assertEqual(transfer.last4_account_number, '')
        self.assertEqual(transfer.masked_account_number, 'xxxxxxxxxxxxxxxx')
        self.assertEqual(transfer.account_number, 'xxxxxxxxxxxxxxxx')

        # Set an account number
        transfer.account_number = '9999999999999991'
        transfer.save()

        # Retrieve account number via decryption
        transfer = TransferMetadata.objects.get(pk=transfer.pk)
        self.assertEqual(transfer.last4_account_number, '9991')
        self.assertEqual(transfer.masked_account_number, 'xxxxxxxxxxxx9991')
        self.assertEqual(transfer.account_number, '9999999999999991')

        # Purge encrypted copy of account number, leaving on the last 4 digits around
        transfer.purge_encrypted_account_number()

        # Make sure only the last 4 digits still exist
        transfer = TransferMetadata.objects.get(pk=transfer.pk)
        self.assertEqual(transfer.last4_account_number, '9991')
        self.assertEqual(transfer.masked_account_number, 'xxxxxxxxxxxx9991')
        self.assertEqual(transfer.account_number, 'xxxxxxxxxxxx9991')
