# Changelog

## Unreleased — Stackquay identity alignment

- Standardize the product name, repository links, local setup messages, OpenAPI title and account emails as Stackquay.
- Update new-install Docker/production defaults, test database identifiers, release artifact naming and operations documentation.
- Document how existing deployments must retain their previous Compose project name and credentials until a deliberate data migration is complete.
- The renamed verification-token signing namespace invalidates previously issued email-verification links; request a new message if needed.
- Preserve the historical v1.0.0 tag and published assets; no new release was created.
- Commercial naming clearance remains pending.

## 1.0.0 — 2026-10-16

First complete Stackquay starter release.

- Django account model with case-insensitive identity uniqueness, optional email-verified public signup, expiring hashed API tokens, profile updates, password changes and email recovery.
- Owner-scoped records CRUD API with validation, search, filters, ordering and pagination.
- Trusted staff administration for accounts, groups, records and token revocation.
- Live OpenAPI documentation and committed schema.
- Windows/macOS/Linux local installer with generated secrets and migrations.
- Single-server Docker Compose production stack with Postgres, Redis, Gunicorn, Caddy HTTPS, production security checks, static assets and health probes.
- Deployment, token/session cleanup, database backup and restore helpers.
- CI for local/database integrations, Windows installation, production container operation and backup/restore.
- Installation, user, API, architecture, security and operations documentation.

Scope: backend starter and self-hosted deployment package. No public hosted service is included.
