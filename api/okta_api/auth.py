"""
OAuth2 client_credentials + private_key_jwt flow for Okta-scoped access
tokens - Okta's recommended (and, for tokens carrying Okta scopes, the
only supported) service-app auth method. The service app signs a
short-lived JWT client assertion with its own RSA private key; Okta only
ever holds the corresponding public key (via the service app's
registered JWKS) - the private key never leaves the caller's environment.

Token endpoint: https://<your-okta-domain>/oauth2/v1/token
"""
from __future__ import annotations

import base64
import json
import time
import uuid

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def build_client_assertion(
    client_id: str, token_url: str, private_key_pem: bytes, expires_in: int = 300
) -> str:
    """
    Build and RS256-sign the JWT client assertion Okta requires for the
    client_credentials + private_key_jwt flow. `expires_in` must be at
    most 3600 seconds (Okta's documented maximum); defaults to 5 minutes
    since a client assertion is effectively single-use in practice.
    """
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)

    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": client_id,
        "sub": client_id,
        "aud": token_url,
        "iat": now,
        "exp": now + expires_in,
        "jti": str(uuid.uuid4()),
    }

    signing_input = (
        f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}"
        f".{_b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    )
    signature = private_key.sign(
        signing_input.encode("ascii"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return f"{signing_input}.{_b64url(signature)}"


def client_credentials_flow(
    org_url: str,
    client_id: str,
    private_key_pem: bytes,
    scopes: list[str],
    timeout: int = 30,
) -> dict:
    """
    Full client_credentials + private_key_jwt flow: build and sign the
    client assertion, POST to /oauth2/v1/token, return the token response
    ({access_token, token_type, expires_in, scope}).
    """
    token_url = f"{org_url.rstrip('/')}/oauth2/v1/token"
    assertion = build_client_assertion(client_id, token_url, private_key_pem)

    response = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "scope": " ".join(scopes),
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": assertion,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()
