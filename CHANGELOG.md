# Changelog

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
