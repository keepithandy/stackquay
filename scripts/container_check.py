#!/usr/bin/env python3
"""Exercise the production image and verify the CI backup/restore round trip."""

import os
import secrets
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django  # noqa: E402

django.setup()
from django.test import Client  # noqa: E402

from core.models import Record, User  # noqa: E402


def main():
    if "--check-restored" in sys.argv:
        assert Record.objects.filter(
            title="Backup round trip", owner__username="container-test"
        ).exists()
        print("PASS: backup retained the user and private record.")
        return
    password = secrets.token_urlsafe(32)
    User.objects.create_user("container-test", "container@example.test", password)
    client = Client(HTTP_HOST="localhost")
    response = client.get("/api/v1/auth/me/", secure=True)
    assert response.status_code == 401
    assert "max-age=" in response["Strict-Transport-Security"]
    response = client.post(
        "/api/v1/auth/login/",
        {"username": "container-test", "password": password},
        content_type="application/json",
        secure=True,
    )
    assert response.status_code == 200
    token = response.json()["token"]
    response = client.post(
        "/api/v1/records/",
        {"title": "Backup round trip"},
        content_type="application/json",
        secure=True,
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 201
    assert response["Cache-Control"] == "no-store"
    response = client.get("/admin/login/", secure=True)
    assert response.status_code == 200
    assert response.cookies["csrftoken"]["secure"]
    from django.contrib.staticfiles.storage import staticfiles_storage

    assert staticfiles_storage.exists("admin/css/base.css")
    assert client.get(staticfiles_storage.url("admin/css/base.css"), secure=True).status_code == 200
    print("PASS: production authentication, record creation, admin CSS and secure headers.")


if __name__ == "__main__":
    main()
