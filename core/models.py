import hashlib
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("email"), name="unique_email_case_insensitive"),
            models.UniqueConstraint(Lower("username"), name="unique_username_case_insensitive"),
        ]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)


class AccessToken(models.Model):
    digest = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)

    @classmethod
    def issue(cls, user):
        raw = secrets.token_urlsafe(48)
        token = cls.objects.create(
            user=user,
            digest=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(hours=settings.TOKEN_TTL_HOURS),
        )
        return raw, token


class Record(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="records"
    )
    title = models.CharField(max_length=200)
    body = models.TextField(max_length=10000, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["owner", "status", "-created_at"])]

    def __str__(self):
        return self.title
