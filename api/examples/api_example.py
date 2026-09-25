"""
Usage examples for okta_api.

Illustrative only - OKTA_ORG_URL/OKTA_API_TOKEN (or client-credentials
inputs) come from the caller's own environment; no real org's domain or
data.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from okta_api import OktaClient, client_credentials_flow

ORG_URL = os.environ["OKTA_ORG_URL"]  # e.g. https://<your-org>.okta.com


def main_ssws():
    """Simple path: a static SSWS API token."""
    client = OktaClient(ORG_URL, os.environ["OKTA_API_TOKEN"], auth_scheme="SSWS")

    # Discover the user profile schema this org actually has - no
    # hardcoded attribute list:
    print("Profile attributes:", client.user_schema_attribute_names())

    for user in client.list_users(limit=50):
        print(user["profile"]["email"])

    for member in client.list_group_members("00g1exampleGroupId"):
        print(member["profile"]["login"])


def main_oauth_service_app():
    """Modern path: OAuth2 client_credentials + private_key_jwt."""
    with open(os.environ["OKTA_PRIVATE_KEY_PATH"], "rb") as f:
        private_key_pem = f.read()

    token_response = client_credentials_flow(
        ORG_URL,
        client_id=os.environ["OKTA_CLIENT_ID"],
        private_key_pem=private_key_pem,
        scopes=["okta.users.read", "okta.groups.read"],
    )

    client = OktaClient(ORG_URL, token_response["access_token"], auth_scheme="Bearer")
    for user in client.list_users():
        print(user["profile"]["email"])


if __name__ == "__main__":
    main_ssws()
