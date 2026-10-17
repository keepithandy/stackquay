# Stackquay

> **Stackquay** is the approved project name. The repository is now `keepithandy/stackquay`. The v1.0.0 release artifacts remain unchanged; this naming update does not publish a new version. External trademark and domain/package namespace clearance are still pending.

**Self-hosted application infrastructure for your next app.** User accounts, private data, an admin dashboard, and a practical path from local install to a single-server production deployment.

[![CI](https://github.com/keepithandy/stackquay/actions/workflows/ci.yml/badge.svg)](https://github.com/keepithandy/stackquay/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-1.0.0-c2e7a8)](https://github.com/keepithandy/stackquay/releases/tag/v1.0.0)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## What you get

- **Accounts:** username/password login, optional email-verified signup, profile updates, password changes, email recovery, expiring sessions, and logout.
- **Your data:** a private records API with create/read/update/delete, UUID identifiers, validation, search, status filters, sorting, and pagination.
- **Administration:** Django's admin dashboard for users, groups, permissions, records, token revocation, and its built-in admin change history.
- **Operations:** Postgres, Redis, Gunicorn, static assets, automatic HTTPS through Caddy, health probes, structured request logs, backups, and restore commands.
- **A reusable repository:** locked dependencies with integrity hashes, database migrations, OpenAPI documentation, automated tests, Windows installation checks, production container checks, and release archives.

Built with Python 3.12, Django 5.2 LTS and Django REST Framework. SQLite keeps local setup small; production uses Postgres and Redis. Start another app with GitHub's **Use this template** button, or fork the repository.

## Install and run

Install Python 3.12 and Git first. No database server is needed for local development.

```text
git clone https://github.com/keepithandy/stackquay.git
cd stackquay
python scripts/setup.py
```

The installer creates `.venv`, installs the locked dependencies, generates a private `.env` with a random secret, and creates the local database. Existing configuration is preserved. The repository is private, so GitHub must recognize your account to clone it.

**Windows PowerShell**

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

**macOS / Linux**

```sh
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

| Open | Purpose |
| --- | --- |
| `http://127.0.0.1:8000/` | Start page |
| `http://127.0.0.1:8000/admin/` | Manage accounts, permissions, and records |
| `http://127.0.0.1:8000/api/docs/` | Interactive API documentation |
| `http://127.0.0.1:8000/api/schema/` | Live OpenAPI schema |
| `http://127.0.0.1:8000/health/ready/` | Database and cache readiness |

There are no default accounts or shared passwords. Create your first administrator with the command above. Local email is printed in the development terminal; no real email is sent until SMTP is configured.

## First API request

Create a normal user in the admin dashboard. Log in to obtain a bearer token, then create a private record. Replace the sample credentials with the account you created.

```sh
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"your-user","password":"your-password"}'

curl -X POST http://127.0.0.1:8000/api/v1/records/ \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"title":"First record","body":"Hello Stackquay","status":"active"}'
```

PowerShell examples, every endpoint, error shapes, and account flows are in [the API guide](docs/API.md). Tokens expire after seven days by default. Password changes and resets revoke all API sessions. The data API always scopes records to their owner, including staff accounts; trusted administrators manage all records through `/admin/`.

## Guides

- [Phase 01 development roadmap](docs/development/phase-01/ROADMAP.md) — frozen baseline, Plex-style authorization gates, release engineering and runtime compatibility.
- [Identity and deployment compatibility](docs/BRAND_TRANSITION.md) — project naming, persistent-volume safeguards, and outstanding clearance checks.


| Guide | What it covers |
| --- | --- |
| [Installation](docs/INSTALL.md) | Windows, macOS/Linux, configuration, troubleshooting |
| [User and admin instructions](docs/USER_GUIDE.md) | Accounts, records, staff roles, recovery |
| [API reference](docs/API.md) | Authentication, endpoints, examples, errors |
| [Production deployment](docs/PRODUCTION.md) | Server requirements, DNS, SMTP, HTTPS, deployment |
| [Operations](docs/OPERATIONS.md) | Backups, restore, updates, logs, incident recovery |
| [Architecture](docs/ARCHITECTURE.md) | Project layout and how to extend the starter |
| [Security](SECURITY.md) | Security model, limits, reporting |
| [Contributing](CONTRIBUTING.md) | Development checks and dependency updates |
| [Changelog](CHANGELOG.md) | Release history |

## Production

**Existing deployment warning:** Changing the Docker Compose project name changes its named-volume namespace. If updating an earlier deployment, follow [identity and compatibility](docs/BRAND_TRANSITION.md) before deploying, retaining the former Compose project identifier and existing credentials until data migration is verified.


The production package targets **one Linux server running Docker Compose**. It includes a reverse proxy, HTTPS certificates, database and cache containers, a non-root application container, persistent data, and a deployment helper.

```sh
python3 scripts/production_env.py \
  --domain api.your-domain.com \
  --smtp-host smtp.your-mail-provider.com \
  --from-email backend@your-domain.com
# Edit .env.production and supply your SMTP credentials.
python3 scripts/ops.py deploy
docker compose --env-file .env.production exec web python manage.py createsuperuser
python3 scripts/smoke.py https://api.your-domain.com
```

Read the [production guide](docs/PRODUCTION.md) before running these commands on a server. **This repository does not provision a server or domain, and no hosted instance is included.** The deployment requires a real domain, reachable ports 80/443, and SMTP for account recovery. No paid service is required for local use.

## Checks

With the development environment installed:

```text
python -m ruff check .
python -m ruff format --check .
python -m coverage run manage.py test --noinput
python -m coverage report
python scripts/check_production.py
```

Use the Python executable inside `.venv`, or activate the environment first. CI also installs from scratch on Windows, tests Postgres/Redis, builds and runs the production container, and exercises a database backup/restore round trip. Docker checks run in GitHub Actions; Docker is not required for local development.

## 1.0 scope

Stackquay is a backend starter for small applications that need users, private CRUD data, and trusted staff administration. Version 1.0 does not include a separate customer frontend, billing, organizations, social login, MFA, file uploads, background jobs, or an audit history of API edits. Admin actions use Django's built-in change log. Application throttles reduce routine abuse; internet-scale traffic needs additional edge controls and capacity planning.

MIT licensed. See [LICENSE](LICENSE).
