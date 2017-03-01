from django.test import TestCase
from ..security import (
    encrypt_account_number,
    decrypt_account_number,
)


class AccountNumberTokenizationTest(TestCase):
    def test_encrypt_account_number(self):
        acct1 = '9999999999999991'
        acct2 = '9999999999999992'
        blob1 = encrypt_account_number(acct1)
        blob2 = encrypt_account_number(acct2)

        self.assertNotEqual(blob1, acct1)
        self.assertEqual(decrypt_account_number(blob1), acct1)

        self.assertNotEqual(blob2, acct2)
        self.assertEqual(decrypt_account_number(blob2), acct2)
