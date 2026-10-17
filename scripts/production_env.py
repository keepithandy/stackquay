#!/usr/bin/env python3
"""Generate a new Docker production env file without displaying secrets."""

import argparse
import os
import re
import secrets
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", required=True, help="Backend hostname, e.g. api.example.com")
    parser.add_argument("--smtp-host", required=True)
    parser.add_argument("--from-email", required=True)
    parser.add_argument("--output", default=".env.production")
    args = parser.parse_args()
    domain = args.domain.lower()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", domain) or "." not in domain:
        parser.error("Use a hostname without https://, a port, or a path.")
    for value in (args.smtp_host, args.from_email):
        if any(c in value for c in "\r\n#='\""):
            parser.error("SMTP settings must be simple single-line values.")
    db_password = secrets.token_hex(32)
    redis_password = secrets.token_hex(32)
    text = f"""# Stackquay production configuration. Keep private; never commit this file.
STACKQUAY_PROJECT_NAME=stackquay
DOMAIN={domain}
DJANGO_DEBUG=0
DJANGO_SECRET_KEY={secrets.token_urlsafe(64)}
DJANGO_ALLOWED_HOSTS={domain},localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://{domain}
DJANGO_CORS_ALLOWED_ORIGINS=
PUBLIC_BASE_URL=https://{domain}
TRUST_PROXY=1
ALLOW_REGISTRATION=0
TOKEN_TTL_HOURS=168
POSTGRES_DB=stackquay
POSTGRES_USER=stackquay
POSTGRES_PASSWORD={db_password}
DATABASE_URL=postgresql://stackquay:{db_password}@db:5432/stackquay
REDIS_PASSWORD={redis_password}
REDIS_URL=redis://:{redis_password}@redis:6379/0
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST={args.smtp_host}
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
DEFAULT_FROM_EMAIL={args.from_email}
"""
    output = Path(args.output)
    with output.open("x", encoding="utf-8") as file:
        file.write(text)
    if os.name != "nt":
        output.chmod(0o600)
    print(f"Created {output}. Set SMTP credentials in that file before deployment.")
    print("Secrets were generated locally and were not displayed.")


if __name__ == "__main__":
    main()
