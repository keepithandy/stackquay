# Security

Version 1.0 uses Django's password hashing, CSRF protection and admin authentication; explicit API permissions; random expiring bearer tokens stored as SHA-256 digests; owner-scoped record queries; verification/recovery links; secure production cookies; HTTPS redirection and HSTS; explicit host/origin lists; and shared-cache throttles.

Production startup rejects weak/missing secrets, wildcard hosts, missing database/cache configuration, non-HTTPS public origins and missing SMTP configuration. The supplied Docker deployment runs the app as a non-root user with a read-only root filesystem. Database and cache ports are not publicly published.

## Trust boundaries

- Administrators and Docker/server operators are trusted. User/group management permissions can confer broad access.
- The public API exposes only records belonging to the caller, including for staff accounts.
- `TRUST_PROXY=1` is safe only when untrusted callers cannot connect directly to Gunicorn and the proxy overwrites forwarded headers.
- Bearer tokens grant the user's API access until revoked/expired. Protect them in client storage and use HTTPS.
- Rate limits are approximate routine abuse controls. They do not replace network/edge defenses against distributed attacks.
- Logs omit account-link tokens, query strings, authorization headers and request bodies. Local console email deliberately displays email content for development.
- Password reset and signup email delivery is synchronous. Generic responses do not remove all timing differences.
- No MFA, social login, per-token scopes, end-user audit trail, organization isolation or compliance certification is claimed by this starter.

Keep dependencies current and rerun the checks after updating. CI audits the pinned production dependencies; a passing audit is a point-in-time result, not a guarantee that future advisories will not affect them.

## Report a vulnerability

Contact the repository owner privately through the GitHub contact method available to you. Do not post credentials, bearer tokens, reset links, database dumps, or exploitable vulnerability details in a public issue. If private vulnerability reporting is enabled for your copy of the repository, use **Security → Report a vulnerability**.

Include the affected version, a minimal reproduction, impact, and suggested mitigation if known. Avoid testing against another person's deployment without permission.
