from django.test import TestCase
from unittest.mock import patch
from wellsfargo.security import (
    encrypt_account_number,
    decrypt_account_number,
    WFRS_SECURITY,
)
from wellsfargo.security.fernet import FernetEncryption
from wellsfargo.security.kms import KMSEncryption
from wellsfargo.security.multi import MultiEncryption
import botocore
import base64
import binascii


FERNET_KEY_1 = b"U3Nyi57e55H2weKVmEPzrGdv18b0bGt3e542rg1J1N8="
FERNET_KEY_2 = b"mbgOpeXTyhhy1DgXreVOt6QMNu2Eem0RmPvJLCndpIw="
FERNET_KEY_3 = b"uK00vxMv9IG-FWvJPxZ4nz5AG3FuvdRj9XMhC8AWY2A="
KMS_KEY_ARN = (
    "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
)

_orig_make_api_call = botocore.client.BaseClient._make_api_call


def mock_make_api_call(self, operation_name, kwargs):
    if operation_name == "Encrypt":
        return {
            "CiphertextBlob": base64.b64encode(kwargs["Plaintext"]),
        }
    if operation_name == "Decrypt":
        resp = {}
        try:
            resp["Plaintext"] = base64.b64decode(kwargs["CiphertextBlob"])
        except binascii.Error:
            pass
        return resp
    return _orig_make_api_call(self, operation_name, kwargs)


def mock_kms(fn):
    def wrapper(*args, **kwargs):
        with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
            resp = fn(*args, **kwargs)
        return resp

    return wrapper


def patch_encryptor(encryptor, **encryptor_kwargs):
    def decorate(fn):
        def wrapper(*args, **kwargs):
            _old_encryptor = WFRS_SECURITY["encryptor"]
            _old_encryptor_kwargs = WFRS_SECURITY["encryptor_kwargs"]
            WFRS_SECURITY["encryptor"] = encryptor
            WFRS_SECURITY["encryptor_kwargs"] = encryptor_kwargs
            resp = fn(*args, **kwargs)
            WFRS_SECURITY["encryptor"] = _old_encryptor
            WFRS_SECURITY["encryptor_kwargs"] = _old_encryptor_kwargs
            return resp

        return wrapper

    return decorate


class AccountNumberTokenizationTest(TestCase):
    @patch_encryptor("wellsfargo.security.fernet.FernetEncryption", key=FERNET_KEY_1)
    def test_facade_fernet(self):
        acct1 = "9999999999999991"
        acct2 = "9999999999999992"
        blob1 = encrypt_account_number(acct1)
        blob2 = encrypt_account_number(acct2)

        self.assertNotEqual(blob1, acct1)
        self.assertEqual(decrypt_account_number(blob1), acct1)

        self.assertNotEqual(blob2, acct2)
        self.assertEqual(decrypt_account_number(blob2), acct2)

    def test_fernet_round_trip(self):
        encryptor = FernetEncryption(FERNET_KEY_1)

        acct1 = "9999999999999991"
        acct2 = "9999999999999992"

        blob1 = encryptor.encrypt(acct1)
        blob2 = encryptor.encrypt(acct2)

        self.assertNotEqual(blob1, acct1)
        self.assertEqual(encryptor.decrypt(blob1), acct1)

        self.assertNotEqual(blob2, acct2)
        self.assertEqual(encryptor.decrypt(blob2), acct2)

    def test_fernet_decrypt(self):
        encryptor = FernetEncryption(FERNET_KEY_1)

        acct1 = "9999999999999991"
        acct2 = "9999999999999992"
        blob1 = b"gAAAAABYxsYabw7ChX1dF66SEsRHmIBZeyTHVvEpSKpS90267Jnxeo2egoNC2By9GrAja9GhccTVzHWYNOI5Kps7U3vcr7D2OKGnrVbe3lpL3rDtYrh3JBg="
        blob2 = b"gAAAAABYxsYapFR9zH883pTKPh0y8SoXPzSSOzYIZIR-06HinrqPfK8BQ0iiEeCMTXlAvaw6yzEM1wjLIBlZtRxpzO5E-tMsxVSn9k02yFr_McU8-t_CN1c="

        self.assertEqual(encryptor.decrypt(blob1), acct1)
        self.assertEqual(encryptor.decrypt(blob2), acct2)

    @mock_kms
    def test_kms_encrypt(self):
        encryptor = KMSEncryption(
            KMS_KEY_ARN,
            region_name="us-east-1",
            encryption_context={"AppName": "Oscar E-Commerce"},
        )
        self.assertEqual(
            encryptor.encrypt("9999999999999991"), b"T1RrNU9UazVPVGs1T1RrNU9UazVNUT09"
        )
        self.assertEqual(
            encryptor.encrypt("9999999999999992"), b"T1RrNU9UazVPVGs1T1RrNU9UazVNZz09"
        )

    @mock_kms
    def test_kms_decrypt(self):
        encryptor = KMSEncryption(
            KMS_KEY_ARN,
            region_name="us-east-1",
            encryption_context={"AppName": "Oscar E-Commerce"},
        )
        self.assertEqual(
            encryptor.decrypt(b"T1RrNU9UazVPVGs1T1RrNU9UazVNUT09"), "9999999999999991"
        )
        self.assertEqual(
            encryptor.decrypt(b"T1RrNU9UazVPVGs1T1RrNU9UazVNZz09"), "9999999999999992"
        )

    @mock_kms
    def test_multi_round_trip(self):
        # Make some data encrypted with key 1
        fernet1 = FernetEncryption(FERNET_KEY_1)
        acct1 = "9999999999999991"
        blob1 = fernet1.encrypt(acct1)

        # Make some data encrypted with key 2
        fernet2 = FernetEncryption(FERNET_KEY_2)
        acct2 = "9999999999999992"
        blob2 = fernet2.encrypt(acct2)

        # Make some data encrypted with key 3
        fernet3 = FernetEncryption(FERNET_KEY_3)
        acct3 = "9999999999999993"
        blob3 = fernet3.encrypt(acct3)

        # Make some data encrypted with KMS
        kms1 = KMSEncryption(
            KMS_KEY_ARN,
            region_name="us-east-1",
            encryption_context={"AppName": "Oscar E-Commerce"},
        )
        acct4 = "9999999999999994"
        blob4 = kms1.encrypt(acct4)

        # Ensure that Fernet can't decrypt data encrypted with other keys
        self.assertEqual(fernet1.decrypt(blob1), acct1)
        self.assertIsNone(fernet1.decrypt(blob2))
        self.assertIsNone(fernet1.decrypt(blob3))
        self.assertIsNone(fernet1.decrypt(blob4))

        self.assertIsNone(fernet2.decrypt(blob1))
        self.assertEqual(fernet2.decrypt(blob2), acct2)
        self.assertIsNone(fernet2.decrypt(blob3))
        self.assertIsNone(fernet2.decrypt(blob4))

        self.assertIsNone(fernet3.decrypt(blob1))
        self.assertIsNone(fernet3.decrypt(blob2))
        self.assertEqual(fernet3.decrypt(blob3), acct3)
        self.assertIsNone(fernet3.decrypt(blob4))

        self.assertIsNone(kms1.decrypt(blob1))
        self.assertIsNone(kms1.decrypt(blob2))
        self.assertIsNone(kms1.decrypt(blob3))
        self.assertEqual(kms1.decrypt(blob4), acct4)

        # Build a multi-encryptor that has knowledge of all the keys
        multi = MultiEncryption(
            encryptors=[
                {
                    "encryptor": "wellsfargo.security.kms.KMSEncryption",
                    "encryptor_kwargs": {
                        "key_id": KMS_KEY_ARN,
                        "region_name": "us-east-1",
                        "encryption_context": {
                            "AppName": "Oscar E-Commerce",
                        },
                    },
                },
                {
                    "encryptor": "wellsfargo.security.fernet.FernetEncryption",
                    "encryptor_kwargs": {
                        "key": FERNET_KEY_3,
                    },
                },
                {
                    "encryptor": "wellsfargo.security.fernet.FernetEncryption",
                    "encryptor_kwargs": {
                        "key": FERNET_KEY_2,
                    },
                },
                {
                    "encryptor": "wellsfargo.security.fernet.FernetEncryption",
                    "encryptor_kwargs": {
                        "key": FERNET_KEY_1,
                    },
                },
            ]
        )

        # Ensure the multi-encryptor can decrypt all of the blobs
        self.assertEqual(multi.decrypt(blob1), acct1)
        self.assertEqual(multi.decrypt(blob2), acct2)
        self.assertEqual(multi.decrypt(blob3), acct3)
        self.assertEqual(multi.decrypt(blob4), acct4)

        # Ensure the multi-encryptor encrypted all new data with KMS, since it's the most preferred
        acct5 = "9999999999999995"
        blob5 = multi.encrypt(acct5)

        self.assertEqual(multi.decrypt(blob5), acct5)

        self.assertIsNone(fernet1.decrypt(blob5))
        self.assertIsNone(fernet2.decrypt(blob5))
        self.assertIsNone(fernet3.decrypt(blob5))
        self.assertEqual(kms1.decrypt(blob5), acct5)
