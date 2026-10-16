# Production deployment

HandyBase 1.0 targets a single Linux server using Docker Compose v2. The repository includes everything needed to run the application stack. It does not create a hosting account, server, domain, or SMTP account.

## Before deployment

You need:

1. A Linux server with Docker Engine, Compose v2, Python 3.12 for the helper scripts, and Git.
2. A domain/subdomain whose DNS points to the server. If it has an AAAA record, IPv6 must reach the same server.
3. Inbound TCP ports 80 and 443 available. UDP 443 is optional for HTTP/3. Use key-based SSH and keep database/cache ports private.
4. A working SMTP service and a permitted sender address for verification and recovery emails.
5. A private destination for off-server backups.

Two CPU cores and 2 GB RAM are a practical starting point for a small deployment, not a measured capacity guarantee. Monitor your own workload before increasing traffic.

## Install the release

Clone with your GitHub account, or transfer the release archive to your server:

```sh
git clone https://github.com/keepithandy/handybase.git
cd handybase
git checkout v1.0.0
```

Run commands from this directory. A release checkout ensures you know which version is deployed. The app is built locally; no container-registry account is needed.

## Generate configuration

```sh
python3 scripts/production_env.py \
  --domain api.your-domain.com \
  --smtp-host smtp.your-mail-provider.com \
  --from-email backend@your-domain.com
```

This creates `.env.production` with new application, Postgres and Redis secrets. It refuses to overwrite an existing file and does not print secrets. Edit `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` directly in that private file. Adjust port/TLS settings to your SMTP service. Set only one of `EMAIL_USE_TLS` and `EMAIL_USE_SSL` to `1`. Use an app password rather than a personal mailbox password when supported.

Restrict file access to the deployment account. Do not commit `.env.production` or share output from `docker compose config`, which can contain expanded secrets. Back up this file privately alongside your database backups. Docker environment values are accessible to trusted Docker administrators.

Leave `ALLOW_REGISTRATION=0` for managed accounts. Enable it only after a real verification email reaches your inbox. Set `DJANGO_CORS_ALLOWED_ORIGINS=https://your-frontend.com` if a separate browser frontend needs API access; otherwise leave it empty.

## Deploy

```sh
python3 scripts/ops.py deploy
docker compose --env-file .env.production exec web python manage.py createsuperuser
python3 scripts/smoke.py https://api.your-domain.com
```

The deployment helper builds the application, starts healthy Postgres/Redis services, runs migrations, collects admin static files, checks production security settings, and waits for service health. Caddy obtains and renews HTTPS certificates when DNS and ports are correct. Initial certificate issuance can take a little time; retry the public smoke check after the proxy is ready.

Open `https://api.your-domain.com/admin/`. Create a normal user, request a password reset through the API, and confirm the email arrives with the right HTTPS hostname. Use that account to create and retrieve a record. Back up the installation and test restore before storing important data.

Startup deliberately fails if required production settings are missing: a strong secret, explicit hosts, Postgres, Redis, HTTPS public origin and CSRF origins, and an SMTP backend/host. Credentials and actual email deliverability still require the operator's verification.

## Network and proxy model

Only Caddy publishes public ports. Postgres, Redis, and Gunicorn are on the private Compose network. `TRUST_PROXY=1` tells Django to trust the proxy's HTTPS signal and `X-Real-IP`; Caddy overwrites the IP header. Do not publish the application container's port to the public internet with that setting enabled. If you use another proxy, it must overwrite these headers and be the only route to the app.

For a managed external Postgres database, replace `DATABASE_URL` and use the provider's TLS requirements, such as `?sslmode=verify-full` with appropriate CA configuration. The supplied in-network database connection does not use TLS. URL-encode special characters in externally supplied connection passwords. The supplied helper generates URL-safe secrets.

## What persists

| Volume | Contents |
| --- | --- |
| `postgres_data` | Accounts, records, tokens, sessions, admin history |
| `static_data` | Collected static assets; regenerable |
| `caddy_data`, `caddy_config` | Certificate and proxy state |

`docker compose down` stops services while preserving named volumes. `down -v` deletes persistent volumes and is used only in disposable CI environments. See [OPERATIONS.md](OPERATIONS.md) for backups, restores and updates.

## Deployment status

Version 1.0 includes and tests the production container stack in CI. A live public deployment is a separate operator action requiring the resources above. No public instance is created by the local installer or by publishing a GitHub release.
