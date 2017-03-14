from django.utils.encoding import force_bytes, force_text
import boto3
import base64


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
        return base64.b64encode(blob)


    def decrypt(self, blob):
        """Accept binary data and return a string"""
        blob = force_bytes(blob)
        blob = base64.b64decode(blob)
        response = self.client.decrypt(
            CiphertextBlob=blob,
            EncryptionContext=self.encryption_context)
        if 'Plaintext' not in response:
            return None
        return force_text(response['Plaintext'])