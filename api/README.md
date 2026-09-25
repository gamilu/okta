# api

Generic Okta Management API client, `okta_api`.

```python
from okta_api import OktaClient, client_credentials_flow

# Simple path: static SSWS token
client = OktaClient(org_url="https://<your-org>.okta.com", token="...", auth_scheme="SSWS")

# Modern path: OAuth2 client_credentials + private_key_jwt
token = client_credentials_flow(org_url, client_id, private_key_pem, scopes=["okta.users.read"])
client = OktaClient(org_url, token["access_token"], auth_scheme="Bearer")

client.user_schema_attribute_names()        # discover, no hardcoded attribute list
for user in client.list_users():
    print(user["profile"]["email"])
```

- `okta_api/client.py` — `OktaClient`: Users/Groups CRUD, `all_pages()`
  following RFC 5988 Link-header pagination (same mechanism as Canvas's
  REST API), self-describing schema
  discovery (`get_user_schema()`/`user_schema_attribute_names()`)
- `okta_api/auth.py` — `client_credentials_flow()` +
  `build_client_assertion()`: real RS256 JWT client-assertion signing for
  Okta's client_credentials + private_key_jwt flow (Okta's required
  method for Okta-scoped OAuth tokens — not a simple client-secret POST)
- `docs/overview.md` — auth (both paths), pagination, schema discovery,
  sourced from Okta's public developer docs
- `examples/api_example.py` — runnable usage demos for both auth paths

Pagination, schema discovery, and CRUD URL construction are verified
against synthetic fixtures. The JWT signing is verified **cryptographically**
— a real RSA keypair is generated, the assertion is signed, and the
signature is independently checked against the public key (including a
negative test confirming a tampered payload correctly fails verification)
— not just checked for producing a plausible-looking string.

**Requires:** `requests`, `cryptography` (`cryptography` is needed for
real RS256 signing).
