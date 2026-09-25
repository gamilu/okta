# Okta — Management API Overview

Sources: [Core Okta API](https://developer.okta.com/docs/reference/core-okta-api/),
[Authenticate with an API token](https://developer.okta.com/docs/guides/create-an-api-token/main/),
[Implement OAuth for Okta with a service app](https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/),
[Schemas](https://developer.okta.com/docs/reference/api/schemas/).

## Basics

- **Base URL:** `https://<your-okta-domain>/api/v1/`.
- **Responses:** JSON.

## Auth — two real paths

- **SSWS API token** — a static token, `Authorization: SSWS <token>`.
  Simple, still very common in real integrations, but Okta explicitly
  recommends moving away from it in favor of OAuth 2.0's short-lived,
  scoped tokens.
- **OAuth 2.0 client_credentials + private_key_jwt** — Okta's recommended
  path for a service app calling Okta's own API with Okta scopes
  (`okta.users.read`, etc.). This is notably **not** a simple client-secret
  POST — Okta requires the client to sign a short-lived JWT assertion with
  its own RSA private key (registered via the service app's JWKS), and
  presents that signed assertion as proof of identity instead of a shared
  secret. Token endpoint: `https://<your-okta-domain>/oauth2/v1/token`.

  Client assertion claims: `iss`/`sub` = client_id, `aud` = the token
  endpoint URL, `exp` ≤ 1 hour from `iat`, `jti` a unique ID. This library
  implements the RS256 signing directly (via `cryptography`) rather than
  wrapping a JWT library, and the signature is verified independently
  (not just "did it produce a string") in this repo's test suite.

## Pagination

RFC 5988 **Link headers**, `rel="next"`, cursor-based via an opaque
`after` query parameter Okta bakes into the returned URL — **the same
mechanism and header format as Canvas's REST API**. The client parses it
with `parse_link_header()`/`all_pages()`.

## Schema discovery

`GET /meta/schemas/user/{schemaId}` — self-describing, but with one real
difference from OData `$metadata` / GraphQL introspection / Salesforce
Describe: there's no single "describe everything" call. A schema ID is
required; `"default"` is Okta's base user profile schema (31 standard
attributes per SCIM Core Schema), and `get_user_schema()` defaults to it.
Custom attributes an org has added show up in the schema's `custom`
section — this is how an integration discovers what's actually on a given
org's user profile without hardcoding attribute names.

## Users / Groups

Standard CRUD shape: `/users`, `/users/{id}`, `/users/{id}/lifecycle/deactivate`;
`/groups`, `/groups/{id}/users` (list/add/remove members). These are
long-stable, widely-documented Okta conventions — not independently
re-verified against a live response this session the way the pagination/
schema/auth mechanics above were, but considered low-risk given how
long-established and widely used they are.
