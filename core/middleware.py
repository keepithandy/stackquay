import hashlib
import json
import logging
import re
import time
import uuid
from ipaddress import ip_address

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger("stackquay.requests")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        message = record.getMessage()
        if record.name.startswith(("django.request", "django.server", "django.security")):
            # Django's default messages may contain password reset URLs and query strings.
            message = "http_event"
        data = {"level": record.levelname, "logger": record.name, "message": message}
        for field in ("request_id", "method", "path", "status", "duration_ms"):
            if hasattr(record, field):
                data[field] = getattr(record, field)
        if record.exc_info:
            # Never include exception text or local variables (which may contain secrets).
            data["exception_type"] = record.exc_info[0].__name__
        return json.dumps(data)


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = str(uuid.uuid4())
        if settings.TRUST_PROXY:
            try:
                request.META["REMOTE_ADDR"] = str(
                    ip_address(request.META.get("HTTP_X_REAL_IP", ""))
                )
            except ValueError:
                pass
        started = time.monotonic()
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        if request.path.startswith("/api/"):
            response["Cache-Control"] = "no-store"
        if request.path.startswith("/accounts/"):
            response["Cache-Control"] = "no-store"
            response["Referrer-Policy"] = "no-referrer"
        logger.info(
            "request",
            extra={
                "request_id": request.request_id,
                "method": request.method,
                "path": re.sub(
                    r"^/accounts/(verify|reset)/.*", r"/accounts/\1/[redacted]/", request.path
                ),
                "status": response.status_code,
                "duration_ms": round((time.monotonic() - started) * 1000, 2),
            },
        )
        return response


class AdminLoginThrottleMiddleware:
    """Bound POST attempts to admin login; shared Redis is required in production."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/admin/login/" and request.method == "POST":
            identity = request.META.get("REMOTE_ADDR", "")
            key = "admin-login:" + hashlib.sha256(identity.encode()).hexdigest()
            if cache.add(key, 1, timeout=60):
                count = 1
            else:
                try:
                    count = cache.incr(key)
                except ValueError:
                    cache.add(key, 1, timeout=60)
                    count = 1
            if count > 10:
                response = JsonResponse(
                    {"detail": "Too many login attempts. Try again in a minute."}, status=429
                )
                response["Retry-After"] = "60"
                return response
        return self.get_response(request)
