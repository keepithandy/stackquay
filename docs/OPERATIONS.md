# Operations

Run from the deployed project directory. Existing installations must preserve their original Compose project identifier using `STACKQUAY_PROJECT_NAME` in `.env.production` until a tested storage migration is completed. Commands assume `.env.production`; pass `--env-file PATH` to `scripts/ops.py` if you keep configuration elsewhere. Do not run two deployment/restore operations concurrently.

## Health and logs

```sh
python3 scripts/smoke.py https://api.your-domain.com
docker compose --env-file .env.production ps
docker compose --env-file .env.production logs --tail 100 web
docker compose --env-file .env.production logs --tail 100 proxy
```

Application request logs are JSON with method, sanitized path, status, duration, and a generated request ID. They omit request bodies, authorization headers, query strings, and raw account-link tokens. The included proxy does not enable access logging. Console email contains account links in development; use SMTP in production.

A healthy process is not proof of healthy dependencies. Use `/health/ready/` for database/cache readiness. It checks connectivity, not SMTP delivery, migration drift, storage capacity, or backup freshness. Monitor those separately.

If readiness fails, inspect database/cache health and logs, available disk space, and connectivity. If the admin login fails behind the proxy, check hostname, CSRF origin, and proxy settings. If a service is unhealthy, Docker's restart policy does not by itself restart it; inspect and resolve the underlying cause before restarting.

## Backup

```sh
python3 scripts/ops.py backup
```

The helper writes a PostgreSQL custom-format dump to `backups/` and refuses to overwrite an existing file. It removes a failed dump, but interrupted or incomplete files still require verification. Backups include personal data and sessions. Keep them private and copy them to off-server storage. An unencrypted file on the same server does not protect against server loss.

Also retain `.env.production`, the deployed Git commit/tag, and any custom code. Store the configuration backup securely; it includes credentials. Caddy can reissue certificates, but its volumes can also be included in a full server backup.

For important data, use a daily schedule and a retention policy appropriate to the app, and perform regular restore drills. PostgreSQL dumps represent a consistent snapshot while the application runs; changes after the snapshot require later backups. This is not point-in-time recovery or high availability.

## Restore

Restore replaces current database contents. Use it only for the intended deployment and after preserving any newer data you need.

```sh
python3 scripts/ops.py restore backups/stackquay-YOUR_TIMESTAMP.dump \
  --confirm-replace-database
python3 scripts/smoke.py https://api.your-domain.com
```

The helper verifies that PostgreSQL can read the dump's archive index, stops web/proxy traffic, restores in a single transaction, reapplies current migrations, and waits for service health. A failed restore leaves traffic stopped so you can investigate. Use matching application and database major versions for a recovery drill. Restoring an older backup discards changes made after it.

CI creates a real user and record, backs up the database, restores it, and confirms those rows survive. Perform your own off-server drill; CI cannot validate your backup storage or retention.

## Updates

1. Read the release notes and migration instructions.
2. Make an off-server backup of the database and configuration.
3. Fetch the new version and check out the exact release tag.
4. Run `python3 scripts/ops.py deploy`.
5. Verify public health, admin login, a normal user's record access, and email delivery.

Migrations are run explicitly before the application is replaced. Some future migrations may require a maintenance window; follow their release notes. Running multiple deployment commands at once can race migrations and static collection.

To roll back code without schema changes, check out the previous tag and redeploy. If a migration is incompatible with the previous version, restore a compatible database backup during a maintenance window. Do not assume every migration is reversible. The Docker image tag is a convenience label; the release tag/commit identifies the source version.

## Daily cleanup

```sh
python3 scripts/ops.py prune
```

Schedule this once per day with your server's scheduler. It removes expired API tokens and expired Django sessions. A new login also prunes that user's expired and excess tokens. Verification/reset links are stateless and require no cleanup.

## Security response

Disable affected accounts or delete their API tokens in the admin dashboard. Rotate compromised passwords. If `DJANGO_SECRET_KEY` is exposed, replace it and restart; this invalidates signed links and browser sessions, but does not revoke independent bearer tokens. Revoke those separately by deleting token rows through the admin dashboard. Rotate database/Redis/SMTP credentials at both ends if they are exposed.

Changing `POSTGRES_PASSWORD` in the env file alone does not change the password of an already initialized database. Coordinate the database role update and connection URL under a maintenance window. Never delete the database volume to rotate a password.
