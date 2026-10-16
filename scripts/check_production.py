#!/usr/bin/env python3
"""Validate production security configuration without contacting external services."""

import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    environment = {
        **os.environ,
        "DJANGO_DEBUG": "0",
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(64),
        "DJANGO_ALLOWED_HOSTS": "api.example.test,localhost,127.0.0.1",
        "DJANGO_CSRF_TRUSTED_ORIGINS": "https://api.example.test",
        "DJANGO_CORS_ALLOWED_ORIGINS": "",
        "DATABASE_URL": "postgresql://handybase:example@localhost:5432/handybase",
        "REDIS_URL": "redis://localhost:6379/0",
        "PUBLIC_BASE_URL": "https://api.example.test",
        "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "EMAIL_HOST": "smtp.example.test",
        "EMAIL_USE_TLS": "1",
        "EMAIL_USE_SSL": "0",
    }
    subprocess.run(  # noqa: S603
        [sys.executable, "manage.py", "check", "--deploy", "--fail-level", "WARNING"],
        cwd=ROOT,
        env=environment,
        check=True,
    )
    for setting, value in (
        ("DJANGO_SECRET_KEY", "weak"),
        ("DJANGO_ALLOWED_HOSTS", "*"),
        ("DATABASE_URL", ""),
        ("REDIS_URL", ""),
        ("PUBLIC_BASE_URL", "http://api.example.test"),
        ("EMAIL_HOST", ""),
        ("DJANGO_CSRF_TRUSTED_ORIGINS", "http://api.example.test"),
        ("DJANGO_CORS_ALLOWED_ORIGINS", "http://frontend.example.test"),
        ("TOKEN_TTL_HOURS", "0"),
        ("DATABASE_URL", "mysql://localhost/db"),
        ("EMAIL_USE_SSL", "1"),
    ):
        result = subprocess.run(  # noqa: S603
            [sys.executable, "manage.py", "check"],
            cwd=ROOT,
            env={**environment, setting: value},
            capture_output=True,
        )
        if result.returncode == 0:
            raise SystemExit(f"FAIL: insecure production setting accepted: {setting}")
    print("PASS: production checks and 11 invalid-configuration checks.")


if __name__ == "__main__":
    main()
