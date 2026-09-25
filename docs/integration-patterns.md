# Okta / Identity Integration Patterns

General patterns for SSO and identity-provisioning integration work,
drawn from personal experience implementing SAML SSO organization-wide
and building the automation around Azure AD identity provisioning at
production scale. Written as transferable patterns, not tied to any
specific institution's or employer's integration code or configuration.

## Authentication vs. provisioning — keep them conceptually separate

- **SSO answers "is this a valid, authenticated user"; it says nothing
  about whether that user has an account, role, or group membership in
  any downstream application.** These are two different problems that
  get conflated constantly. A SAML/OIDC login succeeding is not the same
  event as "this person should now have access to system X" — account
  provisioning needs its own trigger, typically tied to a status change
  in the system of record (an SIS admission status, an HR hire event),
  independent of whatever IdP configuration handles authentication itself.
- **The same distinction applies to SIS/LMS integration** — it's
  worth recognizing as a general identity-integration principle, not an
  Okta-specific one.

## Identity provisioning automation

- **Automate off of status transitions, not off of polling** — the same
  principle as workflow automation elsewhere. Provisioning a downstream
  account the moment an upstream status actually changes (rather than on
  a scheduled poll checking "has anything changed") reduces both latency
  and the chance of a missed window between poll intervals.
- **Deprovisioning deserves the same rigor as provisioning, and usually
  gets less.** It's easy to build a clean onboarding automation and leave
  offboarding as a manual afterthought — but stale access after someone
  leaves is a real security and compliance liability, not just an
  inconvenience. Automated deprovisioning triggered by the same status
  system that triggers provisioning closes this gap structurally instead
  of relying on someone remembering.
- **A break in identity-provisioning integrity is one of the
  highest-blast-radius failure classes in any organization** — it
  doesn't just affect one system, it cascades into every downstream
  application gated on identity (SSO, email, financial systems, the SIS
  itself). Monitoring for provisioning anomalies deserves disproportionate
  attention relative to how simple the provisioning logic itself looks on
  paper.

## Schema and attribute mapping

- **Custom attributes drift, and an integration that hardcodes an
  attribute list will eventually break silently.** An IdP's user schema
  (Okta's included) gets extended with org-specific custom attributes
  over time, often by someone other than whoever owns the integration.
  Discovering the schema (or at minimum, validating against it) rather
  than assuming a fixed attribute set catches this before a mapping
  silently drops or misreads a field.
- **Attribute-mapping logic is exactly the kind of thing that benefits
  from being centrally defined and explicit**, not scattered across
  multiple integration points that each independently decide what a
  given field means. The same "define the business rule once, explicitly"
  principle that applies to grade/attendance qualification logic in LMS
  integrations applies here to
  what counts as "this user's department" or "this user's active status."

## Static tokens vs. short-lived scoped tokens

- **A static credential (an SSWS-style API token, a long-lived API key)
  is operationally simpler but a much larger liability if it leaks** — it
  has no natural expiration and often carries broad access. Preferring a
  short-lived, narrowly-scoped OAuth token (even at the cost of more
  integration complexity, e.g. signing a JWT client assertion) is the
  right default for anything touching identity data specifically, given
  how high the stakes are if that particular integration's credentials
  are ever compromised.
