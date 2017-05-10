from django.utils.encoding import force_bytes, force_text, DjangoUnicodeDecodeError
from botocore.exceptions import ClientError
import boto3
import base64
import binascii


class KMSEncryption(object):
    """
    Encrypt data using AWS KMS

    Provides an alternative to wellsfargo.security.fernet.FernetEncryption, to encrypt
    sensitive data remotely using the AWS KMS API via boto3.

    Usage (with a KMS ARN):

    WFRS_SECURITY = {
        'encryptor': 'wellsfargo.security.kms.KMSEncryption',
        'encryptor_kwargs': {
            'key_id': 'arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012',
            'encryption_context': {
                'AppName': 'Oscar E-Commerce'
            }
        },
    }

    key_id can also use a:

    - Key alias ARN: arn:aws:kms:us-east-1:123456789012:alias/MyAliasName
    - Key alias Name: alias/MyAliasName
    - Globally Unique Key ID: 12345678-1234-1234-1234-123456789012

    For details, see `the boto3 docs <https://boto3.readthedocs.io/en/latest/reference/services/kms.html#KMS.Client.encrypt>`_.
    """
    def __init__(self, key_id, **kwargs):
        self.key_id = key_id
        self.encryption_context = kwargs.pop('encryption_context', {})
        self.client = boto3.client('kms', **kwargs)


    def encrypt(self, value):
        """Accept a string and return binary data"""
        value = force_bytes(value)

        response = self.client.encrypt(
            KeyId=self.key_id,
            Plaintext=value,
            EncryptionContext=self.encryption_context)

        blob = response['CiphertextBlob']
        blob = base64.b64encode(blob)
        return blob


    def decrypt(self, blob):
        """Accept binary data and return a string"""
        blob = force_bytes(blob)
        try:
            blob = base64.b64decode(blob)
        except binascii.Error:
            return None

        try:
            response = self.client.decrypt(
                CiphertextBlob=blob,
                EncryptionContext=self.encryption_context)
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidCiphertextException':
                return None
            raise e

        plain_text = None
        if 'Plaintext' in response:
            try:
                plain_text = force_text(response['Plaintext'])
            except DjangoUnicodeDecodeError:
                pass
        return plain_text
