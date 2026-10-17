# Changelog

## Unreleased — Stackquay brand transition (not a published version)

- Adopt **Stackquay** as the project-facing successor name to HandyBase in the README, local homepage, installer messages, and planning documentation.
- Retain the GitHub repository slug `keepithandy/handybase` until an authorized GitHub Settings rename is performed.
- Preserve the historical HandyBase v1.0.0 release, API routes, Django models and migrations, and deployment configuration. No version 1.1 release is implied.
- Formal trademark and package/domain registry availability checks remain outstanding; see `docs/BRAND_TRANSITION.md`.


## 1.0.0 — 2026-10-16

First complete HandyBase starter release.

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
