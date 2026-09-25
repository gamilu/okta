"""
Generic Okta Management API client.

Base URL: https://<your-okta-domain>/api/v1/
Auth: either a static SSWS API token (Authorization: SSWS <token>) - the
classic, simple approach - or an OAuth2 bearer token obtained via the
client_credentials + private_key_jwt flow (see auth.py), Okta's
recommended modern approach for Okta-scoped access. Both use the same
Authorization header shape at the HTTP level, just a different scheme
prefix.

Pagination: RFC 5988 Link headers (rel="next"), cursor-based via an
opaque `after` parameter baked into the returned URL - the same
mechanism and header format as Canvas's REST API.

Schema discovery: GET /meta/schemas/user/{schemaId} - self-describing,
though unlike OData/GraphQL/Salesforce, Okta doesn't expose a single
"describe everything" call; a schema ID must be supplied
(get_user_schema() defaults to "default", Okta's base user schema).
"""
from __future__ import annotations

import re
from typing import Iterator, Optional

import requests

_LINK_RE = re.compile(r'<([^>]+)>;\s*rel="([^"]+)"')


def parse_link_header(link_header: Optional[str]) -> dict[str, str]:
    """Parse an RFC 5988 Link header into {rel: url}."""
    if not link_header:
        return {}
    return {rel: url for url, rel in _LINK_RE.findall(link_header)}


class OktaClient:
    def __init__(self, org_url: str, token: str, auth_scheme: str = "SSWS", timeout: int = 30):
        """
        auth_scheme: "SSWS" for a classic static API token, or "Bearer"
        for an OAuth2 access token from auth.client_credentials_flow().
        """
        self.org_url = org_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"{auth_scheme} {token}",
            "Accept": "application/json",
        })

    @property
    def _api_base(self) -> str:
        return f"{self.org_url}/api/v1"

    def get(self, path: str, params: Optional[dict] = None) -> requests.Response:
        url = f"{self._api_base}/{path.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response

    def get_json(self, path: str, params: Optional[dict] = None):
        return self.get(path, params).json()

    def all_pages(self, path: str, params: Optional[dict] = None) -> Iterator[dict]:
        """Yield every record across all pages, following rel="next" Link headers."""
        response = self.get(path, params)
        while True:
            payload = response.json()
            if isinstance(payload, list):
                yield from payload
            else:
                yield payload
                return

            next_url = parse_link_header(response.headers.get("Link")).get("next")
            if not next_url:
                return
            response = self.session.get(next_url, timeout=self.timeout)
            response.raise_for_status()

    # --- Users ---

    def list_users(self, **params) -> Iterator[dict]:
        yield from self.all_pages("users", params=params)

    def get_user(self, user_id: str) -> dict:
        return self.get_json(f"users/{user_id}")

    def create_user(
        self, profile: dict, credentials: Optional[dict] = None, activate: bool = True
    ) -> dict:
        body = {"profile": profile}
        if credentials:
            body["credentials"] = credentials
        url = f"{self._api_base}/users"
        response = self.session.post(
            url, json=body, params={"activate": str(activate).lower()}, timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def update_user(self, user_id: str, profile: dict) -> dict:
        url = f"{self._api_base}/users/{user_id}"
        response = self.session.post(url, json={"profile": profile}, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def deactivate_user(self, user_id: str) -> None:
        url = f"{self._api_base}/users/{user_id}/lifecycle/deactivate"
        response = self.session.post(url, timeout=self.timeout)
        response.raise_for_status()

    # --- Groups ---

    def list_groups(self, **params) -> Iterator[dict]:
        yield from self.all_pages("groups", params=params)

    def list_group_members(self, group_id: str) -> Iterator[dict]:
        yield from self.all_pages(f"groups/{group_id}/users")

    def add_user_to_group(self, group_id: str, user_id: str) -> None:
        url = f"{self._api_base}/groups/{group_id}/users/{user_id}"
        response = self.session.put(url, timeout=self.timeout)
        response.raise_for_status()

    def remove_user_from_group(self, group_id: str, user_id: str) -> None:
        url = f"{self._api_base}/groups/{group_id}/users/{user_id}"
        response = self.session.delete(url, timeout=self.timeout)
        response.raise_for_status()

    # --- Schema discovery ---

    def get_user_schema(self, schema_id: str = "default") -> dict:
        """
        Self-describing profile schema - discover every standard + custom
        attribute defined on the user profile, rather than assuming a
        fixed attribute list.
        """
        return self.get_json(f"meta/schemas/user/{schema_id}")

    def user_schema_attribute_names(self, schema_id: str = "default") -> list[str]:
        """Convenience: base + custom attribute names, sorted."""
        schema = self.get_user_schema(schema_id)
        names: set[str] = set()
        for section in ("base", "custom"):
            props = schema.get("definitions", {}).get(section, {}).get("properties", {})
            names.update(props.keys())
        return sorted(names)
