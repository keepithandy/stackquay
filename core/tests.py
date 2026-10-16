import hashlib
import json
import logging
import sys
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from .middleware import JsonFormatter
from .models import AccessToken, Record, User
from .tokens import verification_tokens

PASSWORD = "A-long-useful-password!579"
NEW_PASSWORD = "Another-useful-password!924"


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class BackendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("alice", "alice@example.com", PASSWORD)
        cls.other = User.objects.create_user("bob", "bob@example.com", PASSWORD)
        cls.admin = User.objects.create_superuser("owner", "owner@example.com", PASSWORD)

    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def auth(self, user=None):
        raw, token = AccessToken.issue(user or self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
        return raw, token

    def post(self, path, data=None):
        return self.client.post("/api/v1/auth/" + path + "/", data or {}, format="json")

    def test_health_and_home_are_public(self):
        for path in ("/", "/health/live/", "/health/ready/", "/api/docs/", "/api/schema/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_readiness_hides_dependency_error(self):
        for exception in (ConnectionError("SECRET backend details"), ValueError("SECRET")):
            with patch("core.views.cache.set", side_effect=exception):
                response = self.client.get("/health/ready/")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("SECRET", response.content.decode())

    def test_readiness_detects_bad_cache(self):
        with patch("core.views.cache.get", return_value=None):
            self.assertEqual(self.client.get("/health/ready/").status_code, 503)

    def test_private_api_requires_bearer(self):
        for path in ("/api/v1/records/", "/api/v1/auth/me/"):
            self.assertEqual(self.client.get(path).status_code, 401)

    def test_login_stores_only_hashed_token(self):
        response = self.post("login", {"username": "alice", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        raw = response.data["token"]
        self.assertEqual(AccessToken.objects.get().digest, hashlib.sha256(raw.encode()).hexdigest())
        self.assertNotIn("password", response.data["user"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {raw}")
        self.assertEqual(self.client.get("/api/v1/auth/me/").data["username"], "alice")

    def test_login_caps_sessions(self):
        for _ in range(22):
            AccessToken.issue(self.user)
        self.assertEqual(
            self.post("login", {"username": "alice", "password": PASSWORD}).status_code, 200
        )
        self.assertEqual(AccessToken.objects.filter(user=self.user).count(), 20)

    def test_bad_or_inactive_login(self):
        self.assertEqual(
            self.post("login", {"username": "alice", "password": "wrong"}).status_code, 401
        )
        self.user.is_active = False
        self.user.save()
        self.assertEqual(
            self.post("login", {"username": "alice", "password": PASSWORD}).status_code, 401
        )

    def test_expired_tokens_fail(self):
        _, token = self.auth()
        token.expires_at = timezone.now() - timedelta(seconds=1)
        token.save()
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)

    def test_malformed_and_unknown_authorization_fail(self):
        for value in ("Bearer", "Bearer x y", "Basic abc", "Bearer unknown", "Bearer " + "a" * 300):
            self.client.credentials(HTTP_AUTHORIZATION=value)
            self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)

    def test_logout_revokes_current_session(self):
        self.auth()
        _, other_token = AccessToken.issue(self.user)
        self.assertEqual(self.post("logout").status_code, 204)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)
        self.assertTrue(AccessToken.objects.filter(pk=other_token.pk).exists())

    def test_profile_cannot_change_privileges_or_email(self):
        self.auth()
        response = self.client.patch(
            "/api/v1/auth/me/",
            {
                "first_name": "Alicia",
                "is_superuser": True,
                "email": "hijack@example.com",
                "username": "owner",
                "is_staff": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alicia")
        self.assertEqual(self.user.email, "alice@example.com")
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)
        self.assertEqual(self.user.username, "alice")

    def test_password_change_revokes_all_tokens(self):
        self.auth()
        AccessToken.issue(self.user)
        response = self.post(
            "change-password", {"current_password": PASSWORD, "password": NEW_PASSWORD}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AccessToken.objects.filter(user=self.user).count(), 0)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

    def test_password_change_rejects_bad_current_or_weak_password(self):
        self.auth()
        for current, new in (("wrong", NEW_PASSWORD), (PASSWORD, "short")):
            self.assertEqual(
                self.post(
                    "change-password", {"current_password": current, "password": new}
                ).status_code,
                400,
            )

    def test_admin_password_change_and_deactivation_revoke_tokens(self):
        self.auth()
        self.user.set_password(NEW_PASSWORD)
        self.user.save()
        self.assertFalse(AccessToken.objects.filter(user=self.user).exists())
        self.auth()
        self.user.is_active = False
        self.user.save()
        self.assertFalse(AccessToken.objects.filter(user=self.user).exists())

    def test_registration_disabled_by_default(self):
        self.assertEqual(self.post("register", {}).status_code, 403)
        self.assertEqual(
            self.post("resend-verification", {"email": "alice@example.com"}).status_code, 403
        )

    @override_settings(ALLOW_REGISTRATION=True)
    def test_registration_email_and_one_use_verification(self):
        response = self.post(
            "register", {"username": "newperson", "email": "New@Example.com", "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 202)
        user = User.objects.get(username="newperson")
        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(len(mail.outbox), 1)
        uid, token = (
            urlsafe_base64_encode(force_bytes(user.pk)),
            verification_tokens.make_token(user),
        )
        path = f"/accounts/verify/{uid}/{token}/"
        self.assertContains(self.client.get(path), "Verify your account")
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        response = self.post("verify", {"uid": uid, "token": token})
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active and user.email_verified)
        self.assertEqual(self.post("verify", {"uid": uid, "token": token}).status_code, 400)

    @override_settings(ALLOW_REGISTRATION=True)
    def test_registration_duplicates_are_generic(self):
        for username, email in (("ALICE", "other@example.com"), ("new", "ALICE@example.com")):
            response = self.post(
                "register", {"username": username, "email": email, "password": PASSWORD}
            )
            self.assertEqual(response.status_code, 202)
            self.assertEqual(User.objects.count(), 3)

    @override_settings(ALLOW_REGISTRATION=True)
    def test_registration_weak_password_rejected(self):
        response = self.post(
            "register", {"username": "new", "email": "new@example.com", "password": "123"}
        )
        self.assertEqual(response.status_code, 400)

    @override_settings(ALLOW_REGISTRATION=True)
    def test_resend_does_not_reactivate_disabled_verified_users(self):
        self.user.is_active = False
        self.user.save()
        response = self.post("resend-verification", {"email": self.user.email})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 0)
        token = verification_tokens.make_token(self.user)
        response = self.post(
            "verify", {"uid": urlsafe_base64_encode(force_bytes(self.user.pk)), "token": token}
        )
        self.assertEqual(response.status_code, 400)

    @override_settings(ALLOW_REGISTRATION=True)
    def test_resend_and_browser_verification(self):
        user = User.objects.create_user(
            "pending", "pending@example.com", PASSWORD, is_active=False, email_verified=False
        )
        self.assertEqual(self.post("resend-verification", {"email": user.email}).status_code, 202)
        self.assertEqual(len(mail.outbox), 1)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = verification_tokens.make_token(user)
        path = f"/accounts/verify/{uid}/{token}/"
        self.assertContains(self.client.post(path), "Account verified")
        self.assertContains(self.client.get(path), "Link unavailable")

    def test_invalid_verification_uids(self):
        for uid in ("invalid", "OTk5OTk5", "_", "AA"):
            self.assertEqual(self.post("verify", {"uid": uid, "token": "bad"}).status_code, 400)

    def test_verification_page_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        self.assertEqual(csrf_client.post("/accounts/verify/abc/abc/").status_code, 403)

    def test_reset_request_is_generic_and_sends_correct_link(self):
        self.assertEqual(self.post("password-reset", {"email": self.user.email}).status_code, 202)
        self.assertIn("/accounts/reset/", mail.outbox[0].body)
        response = self.post("password-reset", {"email": "missing@example.com"})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)

    def test_reset_confirmation_revokes_tokens_and_is_one_use(self):
        self.auth()
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        data = {"uid": uid, "token": token, "password": NEW_PASSWORD}
        self.assertEqual(self.post("password-reset/confirm", data).status_code, 200)
        self.assertFalse(AccessToken.objects.filter(user=self.user).exists())
        self.assertEqual(self.post("password-reset/confirm", data).status_code, 400)

    def test_invalid_reset_and_weak_new_password(self):
        for uid in ("invalid", urlsafe_base64_encode(force_bytes(self.user.pk))):
            self.assertEqual(
                self.post(
                    "password-reset/confirm", {"uid": uid, "token": "bad", "password": NEW_PASSWORD}
                ).status_code,
                400,
            )
        token = default_token_generator.make_token(self.user)
        self.assertEqual(
            self.post(
                "password-reset/confirm",
                {
                    "uid": urlsafe_base64_encode(force_bytes(self.user.pk)),
                    "token": token,
                    "password": "short",
                },
            ).status_code,
            400,
        )

    def test_browser_password_reset_revokes_tokens(self):
        self.auth()
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.get(f"/accounts/reset/{uid}/{token}/")
        self.assertEqual(response.status_code, 302)
        response = self.client.post(
            response.url, {"new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD}
        )
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get(response.url), "Password reset")
        self.assertFalse(AccessToken.objects.filter(user=self.user).exists())

    def test_record_crud_and_owner_isolation(self):
        self.auth()
        response = self.client.post(
            "/api/v1/records/", {"title": "First", "owner": self.other.pk}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        pk = response.data["id"]
        self.assertEqual(Record.objects.get(pk=pk).owner, self.user)
        path = f"/api/v1/records/{pk}/"
        self.assertEqual(
            self.client.patch(path, {"status": "active"}, format="json").status_code, 200
        )
        self.auth(self.other)
        self.assertEqual(self.client.get("/api/v1/records/").data["count"], 0)
        for method in (self.client.get, self.client.delete):
            self.assertEqual(method(path).status_code, 404)
        self.assertEqual(
            self.client.patch(path, {"title": "hijack"}, format="json").status_code, 404
        )
        self.auth()
        self.assertEqual(self.client.delete(path).status_code, 204)

    def test_staff_api_is_still_owner_scoped(self):
        Record.objects.create(owner=self.user, title="private")
        self.auth(self.admin)
        self.assertEqual(self.client.get("/api/v1/records/").data["count"], 0)

    def test_record_validation(self):
        self.auth()
        for data in (
            {"title": ""},
            {"title": "x" * 201},
            {"title": "x", "status": "no"},
            {"title": "x", "body": "x" * 10001},
        ):
            self.assertEqual(
                self.client.post("/api/v1/records/", data, format="json").status_code, 400
            )

    def test_record_filter_search_ordering_pagination(self):
        self.auth()
        Record.objects.create(owner=self.user, title="Zebra", status="active")
        Record.objects.create(owner=self.user, title="Apple", status="draft")
        response = self.client.get("/api/v1/records/?status=active&search=zebra")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            self.client.get("/api/v1/records/?ordering=title").data["results"][0]["title"], "Apple"
        )
        self.assertEqual(self.client.get("/api/v1/records/?status=nope").status_code, 400)
        Record.objects.bulk_create([Record(owner=self.user, title=f"row {i}") for i in range(30)])
        response = self.client.get("/api/v1/records/")
        self.assertEqual(len(response.data["results"]), 25)
        self.assertIsNotNone(response.data["next"])

    def test_case_insensitive_database_constraints(self):
        for username, email in (("ALICE", "unique@example.com"), ("unique", "ALICE@example.com")):
            with self.assertRaises(IntegrityError), transaction.atomic():
                User.objects.create_user(username, email, PASSWORD)

    def test_error_envelope_request_id_and_cache_headers(self):
        response = self.client.get("/api/v1/auth/me/", HTTP_X_REQUEST_ID="untrusted")
        self.assertEqual(response.data["error"]["status"], 401)
        self.assertEqual(response.data["request_id"], response["X-Request-ID"])
        self.assertNotEqual(response["X-Request-ID"], "untrusted")
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_auth_rate_limit(self):
        for _ in range(10):
            self.post("login", {})
        response = self.post("login", {})
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response)

    def test_admin_login_rate_limit_and_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        self.assertEqual(
            csrf_client.post(
                "/admin/login/", {"username": "owner", "password": PASSWORD}
            ).status_code,
            403,
        )
        cache.clear()
        for _ in range(10):
            self.client.post("/admin/login/", {"username": "x", "password": "x"})
        self.assertEqual(self.client.post("/admin/login/", {}).status_code, 429)

    def test_admin_permissions_and_token_secrecy(self):
        raw, token = AccessToken.issue(self.user)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/admin/core/user/").status_code, 302)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get("/admin/core/user/").status_code, 200)
        self.assertEqual(self.client.get("/admin/core/user/add/").status_code, 200)
        self.assertEqual(self.client.get("/admin/core/record/").status_code, 200)
        response = self.client.get(f"/admin/core/accesstoken/{token.pk}/change/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(raw, response.content.decode())
        self.assertNotIn(token.digest, response.content.decode())
        self.assertEqual(self.client.get("/admin/core/accesstoken/add/").status_code, 403)

    def test_admin_creates_user_with_email(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            "/admin/core/user/add/",
            {
                "username": "managed",
                "email": "managed@example.com",
                "password1": PASSWORD,
                "password2": PASSWORD,
                "usable_password": "true",
            },
        )
        self.assertEqual(response.status_code, 302, response.content.decode()[:500])
        self.assertTrue(User.objects.get(username="managed").check_password(PASSWORD))

    def test_prune_tokens_command(self):
        _, old = AccessToken.issue(self.user)
        old.expires_at = timezone.now() - timedelta(days=1)
        old.save()
        AccessToken.issue(self.other)
        output = StringIO()
        call_command("prune_tokens", stdout=output)
        self.assertIn("Deleted 1", output.getvalue())
        self.assertEqual(AccessToken.objects.count(), 1)

    @override_settings(TRUST_PROXY=True)
    def test_trusted_proxy_ip_and_invalid_ip(self):
        with patch("core.middleware.logger.info") as log:
            self.client.get(
                "/health/live/", HTTP_X_REAL_IP="203.0.113.4", HTTP_X_FORWARDED_FOR="1.2.3.4"
            )
        self.assertTrue(log.called)
        self.assertEqual(
            self.client.get("/health/live/", HTTP_X_REAL_IP="invalid").status_code, 200
        )

    def test_json_logs_do_not_include_exception_messages(self):
        try:
            raise ValueError("secret password")
        except ValueError:
            record = logging.LogRecord(
                "test", logging.ERROR, "", 1, "safe message", (), sys.exc_info()
            )
        result = JsonFormatter().format(record)
        self.assertNotIn("secret password", result)
        self.assertEqual(json.loads(result)["exception_type"], "ValueError")
