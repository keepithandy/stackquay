# Architecture and extension guide

## Layout

```text
config/                 Django settings, URL routing, WSGI entry point
core/models.py          Custom user, hashed access tokens, private records
core/serializers.py     Input validation and API response fields
core/authentication.py  Bearer authentication and expiry checks
core/views.py           Account flows, records, health probes
core/admin.py           Administration configuration
core/middleware.py      Request IDs, safe logs, proxy IP, admin login throttle
core/signals.py         Token revocation after password/active changes
core/tokens.py          Single-use email verification token generator
core/migrations/        Committed database schema history
core/tests.py           Account, authorization, admin, data and recovery tests
templates/              Start page and account email/browser forms
scripts/                Install, deployment, backup/restore, verification
deploy/Caddyfile         HTTPS proxy configuration
docs/openapi.yaml       Generated API contract
```

## Requests

Caddy terminates HTTPS and forwards to Gunicorn. Django applies host/security checks and middleware. API requests authenticate a bearer token by its SHA-256 digest, check permissions, apply throttles, and validate JSON. The records queryset always begins with the authenticated owner filter.

The admin dashboard uses Django's session authentication and model permissions. It is intentionally a trusted management surface. Staff can manage cross-user records only if granted the relevant model permissions. Do not grant user/group management permissions to untrusted staff.

## Data and account state

`User` extends Django's `AbstractUser` from the first migration, so new projects can add fields without swapping out the built-in user model later. Email and username have case-insensitive uniqueness constraints. Public signup creates an inactive, unverified user; verification atomically activates it and marks the email verified. Administrator-created users are verified by default.

`AccessToken` stores only a digest, user, creation date, and expiry. Random raw tokens are returned at issuance only. Password/active-state changes through model saves revoke API tokens. Use model saves or account services when changing credentials: direct queryset updates, bulk updates and raw SQL bypass signals and must explicitly revoke tokens. Deactivation is checked on every bearer-authenticated request, even if token rows remain.

`Record` stores a UUID, owner, title, body, status, and timestamps. An owner/status/creation index supports typical list requests. The API uses last-write-wins editing. This sample resource is meant to be extended or replaced with your application's data model.

## Add a resource

1. Add a Django model with an explicit owner relationship if the data is private.
2. Create and commit its migration: `python manage.py makemigrations`.
3. Create an explicit-field serializer. Keep owner and privilege fields server-controlled.
4. Add a viewset whose queryset filters by the caller; assign owner in `perform_create`.
5. Register its route and admin class if needed.
6. Test cross-user read, write and delete attempts alongside successful requests.
7. Regenerate `docs/openapi.yaml` and update the API guide.

Model customizations should be made before the first production data is stored. Once deployed, preserve migration history and add new migrations instead of editing ones already applied.

## Cache, email, and scale

Local development uses SQLite and per-process memory caching. Production requires Postgres and shared Redis so all workers share throttle state. Redis is used for temporary throttle data and health checks, not as the source of truth for records or sessions. Browser sessions live in the database.

Email is synchronous with a 10-second SMTP timeout. Low-volume account email is within the 1.0 scope; a high-volume application should introduce a durable job queue and delivery monitoring. Public signup/reset responses avoid directly disclosing account existence, but timing differences are not eliminated.

Two Gunicorn workers, a 30-second request timeout, and recycling after roughly 1,000 requests are starting defaults. This is a single-server starter with no high-availability, background processing or file storage subsystem. Load-test your actual app before changing those limits or adding infrastructure.

## Upstream references

- [Django 5.2 documentation](https://docs.djangoproject.com/en/5.2/)
- [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [REST Framework authentication](https://www.django-rest-framework.org/api-guide/authentication/)
- [REST Framework throttling limitations](https://www.django-rest-framework.org/api-guide/throttling/)
- [Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
