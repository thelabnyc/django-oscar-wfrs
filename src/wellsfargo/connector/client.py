from datetime import timedelta
from requests.auth import HTTPBasicAuth
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
from ..settings import (
    WFRS_GATEWAY_COMPANY_ID,
    WFRS_GATEWAY_ENTITY_ID,
    WFRS_GATEWAY_API_HOST,
    WFRS_GATEWAY_CONSUMER_KEY,
    WFRS_GATEWAY_CONSUMER_SECRET,
    WFRS_GATEWAY_CLIENT_CERT_PATH,
    WFRS_GATEWAY_PRIV_KEY_PATH,
)
from ..security import encrypt_pickle, decrypt_pickle
import requests
import logging
import uuid

logger = logging.getLogger(__name__)


class BearerTokenAuth(requests.auth.AuthBase):
    def __init__(self, api_key):
        self.api_key = api_key

    def __call__(self, request):
        request.headers["Authorization"] = "Bearer %s" % self.api_key
        return request


class WFRSAPIKey:
    def __init__(self, api_key, expires_on):
        self.api_key = api_key
        self.expires_on = expires_on

    @property
    def is_expired(self):
        # Force key rotation 10 minutes before it actually expires
        expires_on = self.expires_on - timedelta(minutes=10)
        now = timezone.now()
        return now >= expires_on

    @property
    def ttl(self):
        return int((self.expires_on - timezone.now()).total_seconds())

    def __str__(self):
        return "<WFRSAPIKey expires_on=[%s]>" % self.expires_on


class WFRSGatewayAPIClient:
    company_id = WFRS_GATEWAY_COMPANY_ID
    entity_id = WFRS_GATEWAY_ENTITY_ID
    api_host = WFRS_GATEWAY_API_HOST
    consumer_key = WFRS_GATEWAY_CONSUMER_KEY
    consumer_secret = WFRS_GATEWAY_CONSUMER_SECRET
    client_cert_path = WFRS_GATEWAY_CLIENT_CERT_PATH
    priv_key_path = WFRS_GATEWAY_PRIV_KEY_PATH
    scopes = [
        "PLCCA-Prequalifications",
        "PLCCA-Applications",
        "PLCCA-Payment-Calculations",
        "PLCCA-Transactions-Authorization",
        "PLCCA-Transactions-Charge",
        "PLCCA-Transactions-Authorization-Charge",
        "PLCCA-Transactions-Return",
        "PLCCA-Transactions-Cancel-Authorization",
        "PLCCA-Transactions-Void-Return",
        "PLCCA-Transactions-Void-Sale",
        "PLCCA-Transactions-Timeout-Authorization-Charge",
        "PLCCA-Transactions-Timeout-Return",
        "PLCCA-Account-Details",
    ]

    cache_version = 1

    @property
    def cache_key(self):
        return "wfrs-gateway-api-key-{api_host}-{consumer_key}".format(
            api_host=self.api_host, consumer_key=self.consumer_key
        )

    def api_get(self, path, **kwargs):
        return self.make_api_request("get", path, **kwargs)

    def api_post(self, path, **kwargs):
        return self.make_api_request("post", path, **kwargs)

    def make_api_request(self, method, path, client_request_id=None, **kwargs):
        url = "https://{host}{path}".format(host=self.api_host, path=path)
        # Setup authentication
        auth = BearerTokenAuth(self.get_api_key().api_key)
        cert = None
        if self.client_cert_path and self.priv_key_path:
            cert = (self.client_cert_path, self.priv_key_path)
        # Build headers
        request_id = (
            str(uuid.uuid4()) if client_request_id is None else str(client_request_id)
        )
        headers = {
            "request-id": request_id,
            "gateway-company-id": self.company_id,
            "gateway-entity-id": self.entity_id,
        }
        if client_request_id is not None:
            headers["client-request-id"] = str(client_request_id)
        # Send request
        logger.info(
            "Sending WFRS Gateway API request. URL=[%s], RequestID=[%s]",
            url,
            request_id,
        )
        request_fn = getattr(requests, method)
        resp = request_fn(url, auth=auth, cert=cert, headers=headers, **kwargs)
        logger.info(
            "WFRS Gateway API request returned. URL=[%s], RequestID=[%s], Status=[%s]",
            url,
            request_id,
            resp.status_code,
        )
        # Check response for errors
        if resp.status_code == 400:
            resp_data = resp.json()
            errors = []
            for err in resp_data.get("errors", []):
                exc = ValidationError(err["description"], code=err["error_code"])
                errors.append(exc)
            raise ValidationError(errors)
        # Return response
        return resp

    def get_api_key(self):
        # Check for a cached key
        key_obj = self.get_cached_api_key()
        if key_obj is None:
            key_obj = self.generate_api_key()
            self.store_cached_api_key(key_obj)
        return key_obj

    def get_cached_api_key(self):
        # Try to get an API key from cache
        encrypted_obj = cache.get(self.cache_key, version=self.cache_version)
        if encrypted_obj is None:
            return None
        # Try to decrypt the object we got from cache
        try:
            key_obj = decrypt_pickle(encrypted_obj)
        except Exception as e:
            logger.exception(e)
            return None
        # Check if the key is expired
        if key_obj.is_expired:
            return None
        # Return the key
        return key_obj

    def store_cached_api_key(self, key_obj):
        # Pickle and encrypt the key object
        encrypted_obj = encrypt_pickle(key_obj)
        # Store it in Django's cache for later
        cache.set(
            self.cache_key, encrypted_obj, key_obj.ttl, version=self.cache_version
        )

    def generate_api_key(self):
        url = "https://{host}/token".format(host=self.api_host)
        auth = HTTPBasicAuth(self.consumer_key, self.consumer_secret)
        cert = (self.client_cert_path, self.priv_key_path)
        req_data = {
            "grant_type": "client_credentials",
            "scope": " ".join(self.scopes),
        }
        resp = requests.post(url, auth=auth, cert=cert, data=req_data)
        resp.raise_for_status()
        resp_data = resp.json()
        expires_on = timezone.now() + timedelta(seconds=resp_data["expires_in"])
        logger.info("Generated new WFRS API Key. ExpiresIn=[%s]", expires_on)
        key_obj = WFRSAPIKey(api_key=resp_data["access_token"], expires_on=expires_on)
        return key_obj
