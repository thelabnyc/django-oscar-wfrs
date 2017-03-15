from django.test import TestCase
from mock import patch
from wellsfargo.security import (
    encrypt_account_number,
    decrypt_account_number,
    WFRS_SECURITY,
)
from wellsfargo.security.fernet import FernetEncryption
from wellsfargo.security.kms import KMSEncryption
import botocore
import base64

FERNET_KEY = b'U3Nyi57e55H2weKVmEPzrGdv18b0bGt3e542rg1J1N8='
KMS_KEY_ARN = 'arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012'

_orig_make_api_call = botocore.client.BaseClient._make_api_call


def mock_make_api_call(self, operation_name, kwargs):
    if operation_name == 'Encrypt':
        return {
            "CiphertextBlob": base64.b64encode(kwargs["Plaintext"]),
        }
    if operation_name == 'Decrypt':
        return {
            "Plaintext": base64.b64decode(kwargs["CiphertextBlob"]),
        }
    return _orig_make_api_call(self, operation_name, kwargs)


def mock_kms(fn):
    def wrapper(*args, **kwargs):
        with patch('botocore.client.BaseClient._make_api_call', new=mock_make_api_call):
            resp = fn(*args, **kwargs)
        return resp
    return wrapper


def patch_encryptor(encryptor, **encryptor_kwargs):
    def decorate(fn):
        def wrapper(*args, **kwargs):
            _old_encryptor = WFRS_SECURITY['encryptor']
            _old_encryptor_kwargs = WFRS_SECURITY['encryptor_kwargs']
            WFRS_SECURITY['encryptor'] = encryptor
            WFRS_SECURITY['encryptor_kwargs'] = encryptor_kwargs
            resp = fn(*args, **kwargs)
            WFRS_SECURITY['encryptor'] = _old_encryptor
            WFRS_SECURITY['encryptor_kwargs'] = _old_encryptor_kwargs
            return resp
        return wrapper
    return decorate


class AccountNumberTokenizationTest(TestCase):

    @patch_encryptor('wellsfargo.security.fernet.FernetEncryption', key=FERNET_KEY)
    def test_facade_fernet(self):
        acct1 = '9999999999999991'
        acct2 = '9999999999999992'
        blob1 = encrypt_account_number(acct1)
        blob2 = encrypt_account_number(acct2)

        self.assertNotEqual(blob1, acct1)
        self.assertEqual(decrypt_account_number(blob1), acct1)

        self.assertNotEqual(blob2, acct2)
        self.assertEqual(decrypt_account_number(blob2), acct2)


    def test_fernet_round_trip(self):
        encryptor = FernetEncryption(FERNET_KEY)

        acct1 = '9999999999999991'
        acct2 = '9999999999999992'

        blob1 = encryptor.encrypt(acct1)
        blob2 = encryptor.encrypt(acct2)

        self.assertNotEqual(blob1, acct1)
        self.assertEqual(encryptor.decrypt(blob1), acct1)

        self.assertNotEqual(blob2, acct2)
        self.assertEqual(encryptor.decrypt(blob2), acct2)


    def test_fernet_decrypt(self):
        encryptor = FernetEncryption(FERNET_KEY)

        acct1 = '9999999999999991'
        acct2 = '9999999999999992'
        blob1 = b'gAAAAABYxsYabw7ChX1dF66SEsRHmIBZeyTHVvEpSKpS90267Jnxeo2egoNC2By9GrAja9GhccTVzHWYNOI5Kps7U3vcr7D2OKGnrVbe3lpL3rDtYrh3JBg='
        blob2 = b'gAAAAABYxsYapFR9zH883pTKPh0y8SoXPzSSOzYIZIR-06HinrqPfK8BQ0iiEeCMTXlAvaw6yzEM1wjLIBlZtRxpzO5E-tMsxVSn9k02yFr_McU8-t_CN1c='

        self.assertEqual(encryptor.decrypt(blob1), acct1)
        self.assertEqual(encryptor.decrypt(blob2), acct2)


    @mock_kms
    def test_kms_encrypt(self):
        encryptor = KMSEncryption(KMS_KEY_ARN, region_name='us-east-1', encryption_context={
            'AppName': 'Oscar E-Commerce'
        })
        self.assertEqual(encryptor.encrypt('9999999999999991'), b'T1RrNU9UazVPVGs1T1RrNU9UazVNUT09')
        self.assertEqual(encryptor.encrypt('9999999999999992'), b'T1RrNU9UazVPVGs1T1RrNU9UazVNZz09')


    @mock_kms
    def test_kms_decrypt(self):
        encryptor = KMSEncryption(KMS_KEY_ARN, region_name='us-east-1', encryption_context={
            'AppName': 'Oscar E-Commerce'
        })
        self.assertEqual(encryptor.decrypt(b'T1RrNU9UazVPVGs1T1RrNU9UazVNUT09'), '9999999999999991')
        self.assertEqual(encryptor.decrypt(b'T1RrNU9UazVPVGs1T1RrNU9UazVNZz09'), '9999999999999992')
