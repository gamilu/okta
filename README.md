# okta

Personal reference repo + a working Python client library for **Okta**
(identity/SSO), covering its Management API.

**Scope:** everything here is written from general platform knowledge and
Okta's own public developer documentation, plus general identity-
integration patterns from personal experience — expressed as transferable
patterns only. Nothing here is derived from, or contains, source code,
business logic, data, or configuration belonging to any specific employer
or institution.

## Design philosophy

Schema is discovered at runtime where the vendor supports it, rather than
hardcoded.

| Aspect | Mechanism |
|---|---|
| Pagination | RFC 5988 Link headers, `rel="next"` — the same standard mechanism Canvas's REST API uses |
| Schema discovery | `GET /meta/schemas/user/{schemaId}` — self-describing, though (unlike OData/GraphQL/Salesforce) there's no single "describe everything" call; a schema ID is required |
| Auth | Two real paths: a static SSWS token (simple, discouraged by Okta), or OAuth2 `client_credentials` + `private_key_jwt` (Okta's recommended, and only supported, method for Okta-scoped tokens — genuinely implemented here with real RS256 JWT signing via `cryptography`, verified cryptographically in this repo's test suite) |

## Modules

- **`api/`** — `okta_api` library: Users/Groups CRUD, Link-header
  pagination, self-describing user-schema discovery, and the
  `client_credentials` + `private_key_jwt` OAuth flow
- **`docs/integration-patterns.md`** — personal expertise: identity
  provisioning/deprovisioning automation, auth-vs-provisioning
  separation, schema drift, static-vs-scoped-token tradeoffs — general
  patterns only

See `api/README.md` for usage examples and links to `api/docs/overview.md`.

**Requires:** `requests`, `cryptography`.
