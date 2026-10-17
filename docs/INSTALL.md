# Installation

## Requirements

- Python **3.12** is the supported and CI-tested runtime.
- Git, or download and extract the release ZIP.
- Internet access for the first dependency installation.
- Docker Compose v2 only if you want the production stack.

Keep the entire project folder together. Run commands from that folder. Files in `.venv`, `.env`, and `db.sqlite3` are local state and should never be committed.

## Windows

Open PowerShell in the project folder:

```powershell
python --version
python scripts/setup.py
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

No PowerShell activation-policy change is needed. Use the explicit `.venv` executable as shown. When entering a password for the administrator, the terminal deliberately displays no characters.

To activate instead, use `.\.venv\Scripts\Activate.ps1` if your current policy allows it. Then `python` refers to the project environment.

## macOS / Linux

```sh
python3 --version
python3 scripts/setup.py
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

On systems that separate Python's venv support into an OS package, install that support before running the installer. Do not use `sudo pip` or install this project's dependencies into the OS Python.

## Manual installation

If you want to control each step:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-dev.txt
cp .env.example .env
```

Generate a key with `.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(64))"` and put it in `DJANGO_SECRET_KEY` in `.env`. Then run `manage.py migrate`, `manage.py createsuperuser`, and `manage.py runserver` using the environment's Python. Windows uses `.venv\Scripts\python.exe` and `Copy-Item .env.example .env`.

## Configuration

`.env` supports simple `KEY=value` entries and comment lines. Values already supplied through the process environment take precedence. Do not use shell interpolation or multiline values in `.env`. Restart the process after changes.

| Setting | Development default | Purpose |
| --- | --- | --- |
| `DJANGO_DEBUG` | `1` in generated local file | Development diagnostics; production requires `0` |
| `DJANGO_SECRET_KEY` | Generated randomly | At least 50 characters; keep secret |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Accepted HTTP hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Local HTTP origins | Allowed browser origins for admin/forms |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Empty | Optional frontend origins allowed to call the API |
| `DATABASE_URL` | Empty | Local SQLite; use `postgresql://...` for Postgres |
| `REDIS_URL` | Empty | Local per-process memory cache; shared Redis in production |
| `PUBLIC_BASE_URL` | `http://localhost:8000` | Trusted origin used in account emails |
| `ALLOW_REGISTRATION` | `0` | Set `1` to allow email-verified public signup |
| `TOKEN_TTL_HOURS` | `168` | API session lifetime, between 1 and 720 hours |
| `TRUST_PROXY` | `0` | Set `1` only behind the supplied isolated proxy |
| `EMAIL_BACKEND` | Console | SMTP required in production |
| `EMAIL_HOST`, `EMAIL_PORT` | Empty, `587` | SMTP endpoint |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Empty | SMTP credentials |
| `EMAIL_USE_TLS`, `EMAIL_USE_SSL` | `1`, `0` | STARTTLS vs direct TLS; do not enable both |
| `DEFAULT_FROM_EMAIL` | `stackquay@localhost` | Sender address; use a verified production sender |

Production requirements are enforced at startup. See [PRODUCTION.md](PRODUCTION.md).

## Verify your installation

With the development server running, use another terminal:

```text
python scripts/smoke.py http://127.0.0.1:8000
```

Both health checks should pass. Log into `/admin/`, create a normal user, and try an API request from [API.md](API.md).

## Troubleshooting

**Python is not found:** install Python 3.12, enable its PATH option, and reopen the terminal. On some Windows installations use `py -3.12 scripts/setup.py`.

**Virtual environment or temporary-directory error:** the installer creates a project-local temporary directory. Confirm the project folder is writable and is not being locked by another program.

**Network/proxy/certificate errors during install:** the installer must reach your configured Python package index. Use your organization's trusted proxy/certificate configuration. Do not disable TLS validation or remove hash checks.

**Weak or missing secret:** rerun the installer only if you have not created `.env`, or generate a new secret and set it in your existing file. The installer never overwrites that file.

**Port 8000 is in use:** run `manage.py runserver 8001`; update `PUBLIC_BASE_URL` and the local CSRF origins to match.

**Missing database table:** run `manage.py migrate` using the project environment.

**Invalid host or CSRF failure:** use the hostname in `DJANGO_ALLOWED_HOSTS` and the correct origin, including scheme and port, in `DJANGO_CSRF_TRUSTED_ORIGINS`. Restart after editing.

**Email is only in the terminal:** that is the intended local default. Configure SMTP to send real email.

**Tests complain about `testserver`:** run them with Django's test runner, `manage.py test`; it adds the test hostname automatically.
