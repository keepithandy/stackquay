import logging

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_http_methods
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, generics, status, viewsets
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .models import AccessToken, Record, User
from .serializers import (
    ChangePasswordSerializer,
    DetailSerializer,
    EmailSerializer,
    HealthSerializer,
    LoginSerializer,
    RecordSerializer,
    RegisterSerializer,
    ResetConfirmSerializer,
    TokenSerializer,
    UserSerializer,
    VerifySerializer,
    check_password,
)
from .tokens import verification_tokens

logger = logging.getLogger("stackquay.accounts")
GENERIC_EMAIL = "If the account is eligible, an email with next steps has been sent."


def user_from_uid(uid):
    try:
        return User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
    except (ValueError, TypeError, OverflowError, UnicodeDecodeError, User.DoesNotExist):
        return None


def verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = verification_tokens.make_token(user)
    url = f"{settings.PUBLIC_BASE_URL}/accounts/verify/{uid}/{token}/"
    send_mail(
        "Verify your Stackquay account",
        f"Open this link and press Verify account to finish signing up:\n{url}\n\n"
        "This link expires in one hour. If you did not request this, ignore this email.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )


class PublicAuthView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RegisterView(PublicAuthView):
    serializer_class = RegisterSerializer

    @extend_schema(responses={202: DetailSerializer})
    def post(self, request):
        if not settings.ALLOW_REGISTRATION:
            raise PermissionDenied(
                "Public registration is disabled. Ask an administrator for an account."
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if (
            not User.objects.filter(username__iexact=data["username"]).exists()
            and not User.objects.filter(email__iexact=data["email"]).exists()
        ):
            try:
                with transaction.atomic():
                    user = User.objects.create_user(**data, is_active=False, email_verified=False)
                    verification_email(user)
            except IntegrityError:
                pass  # A concurrent registration won; do not reveal account existence.
        return Response({"detail": GENERIC_EMAIL}, status=status.HTTP_202_ACCEPTED)


class ResendVerificationView(PublicAuthView):
    serializer_class = EmailSerializer

    @extend_schema(responses={202: DetailSerializer})
    def post(self, request):
        if not settings.ALLOW_REGISTRATION:
            raise PermissionDenied("Public registration is disabled.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"], is_active=False, email_verified=False
        ).first()
        if user:
            verification_email(user)
        return Response({"detail": GENERIC_EMAIL}, status=202)


def activate_user(uid, token):
    with transaction.atomic():
        user = user_from_uid(uid)
        if user is None:
            return False
        user = User.objects.select_for_update().get(pk=user.pk)
        if (
            user.is_active
            or user.email_verified
            or not verification_tokens.check_token(user, token)
        ):
            return False
        user.is_active = True
        user.email_verified = True
        user.save(update_fields=["is_active", "email_verified"])
    return True


class VerifyView(PublicAuthView):
    serializer_class = VerifySerializer

    @extend_schema(responses=DetailSerializer)
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not activate_user(**serializer.validated_data):
            raise ValidationError("Invalid or expired verification link.")
        return Response({"detail": "Account verified. You can now log in."})


@require_http_methods(["GET", "POST"])
def verification_page(request, uid, token):
    # GET never changes account state; link scanners cannot activate accounts.
    user = user_from_uid(uid)
    valid = (
        user is not None
        and not user.is_active
        and not user.email_verified
        and verification_tokens.check_token(user, token)
    )
    verified = request.method == "POST" and activate_user(uid, token)
    return render(request, "accounts/verify.html", {"valid": valid, "verified": verified})


class LoginView(PublicAuthView):
    serializer_class = LoginSerializer

    def get_authenticate_header(self, request):
        return "Bearer"

    @extend_schema(responses=TokenSerializer)
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request, **serializer.validated_data)
        if user is None:
            raise AuthenticationFailed("Invalid credentials or inactive account.")
        with transaction.atomic():
            # Serialize issuance against password changes, resets and deactivation.
            user = User.objects.select_for_update().get(pk=user.pk)
            if not user.is_active or not user.check_password(serializer.validated_data["password"]):
                raise AuthenticationFailed("Invalid credentials or inactive account.")
            AccessToken.objects.filter(user=user, expires_at__lte=timezone.now()).delete()
            # Bound stored sessions; oldest sessions are removed above 20.
            keep = list(
                AccessToken.objects.filter(user=user)
                .order_by("-created_at")
                .values_list("pk", flat=True)[:19]
            )
            AccessToken.objects.filter(user=user).exclude(pk__in=keep).delete()
            raw, token = AccessToken.issue(user)
        return Response(
            {"token": raw, "expires_at": token.expires_at, "user": UserSerializer(user).data}
        )


class LogoutView(generics.GenericAPIView):
    serializer_class = DetailSerializer

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        request.auth.delete()
        return Response(status=204)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer

    @extend_schema(responses=DetailSerializer)
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            if not user.check_password(data["current_password"]):
                raise ValidationError({"current_password": "Incorrect password."})
            check_password(data["password"], user)
            user.set_password(data["password"])
            user.save(update_fields=["password"])
        return Response({"detail": "Password changed. Log in again on all devices."})


class PasswordResetView(PublicAuthView):
    serializer_class = EmailSerializer

    @extend_schema(responses={202: DetailSerializer})
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form = PasswordResetForm(serializer.validated_data)
        form.is_valid()
        from urllib.parse import urlparse

        origin = urlparse(settings.PUBLIC_BASE_URL)
        form.save(
            use_https=origin.scheme == "https",
            from_email=settings.DEFAULT_FROM_EMAIL,
            domain_override=origin.netloc,
            email_template_name="accounts/reset_email.txt",
            subject_template_name="accounts/reset_subject.txt",
        )
        return Response({"detail": GENERIC_EMAIL}, status=202)


class PasswordResetConfirmView(PublicAuthView):
    serializer_class = ResetConfirmSerializer

    @extend_schema(responses=DetailSerializer)
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            user = user_from_uid(data["uid"])
            if user is None:
                raise ValidationError("Invalid or expired reset token.")
            user = User.objects.select_for_update().get(pk=user.pk)
            if not user.is_active or not default_token_generator.check_token(user, data["token"]):
                raise ValidationError("Invalid or expired reset token.")
            check_password(data["password"], user)
            user.set_password(data["password"])
            user.save(update_fields=["password"])
        return Response({"detail": "Password reset. Log in again on all devices."})


@extend_schema(parameters=[OpenApiParameter("status", str, enum=Record.Status.values)])
class RecordViewSet(viewsets.ModelViewSet):
    serializer_class = RecordSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "body"]
    ordering_fields = ["created_at", "updated_at", "title"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Record.objects.none()
        queryset = Record.objects.filter(owner=self.request.user)
        state = self.request.query_params.get("status")
        if state:
            if state not in Record.Status.values:
                raise ValidationError({"status": "Use draft, active, or archived."})
            queryset = queryset.filter(status=state)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LiveView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []
    serializer_class = HealthSerializer

    @extend_schema(responses=HealthSerializer)
    def get(self, request):
        return Response({"status": "ok"})


class ReadyView(LiveView):
    @extend_schema(responses={200: HealthSerializer, 503: HealthSerializer})
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            cache_key = "readiness-probe"
            cache.set(cache_key, "ok", timeout=10)
            if cache.get(cache_key) != "ok":
                raise RuntimeError("cache unavailable")
        except (DatabaseError, ConnectionError, RuntimeError, OSError):
            return Response({"status": "unavailable"}, status=503)
        except Exception as exc:
            # Backend-specific Redis errors also become a sanitized readiness failure.
            logger.warning(
                "readiness_dependency_failure", extra={"exception_type": type(exc).__name__}
            )
            return Response({"status": "unavailable"}, status=503)
        return Response({"status": "ok"})


def home(request):
    return render(request, "home.html")


def plain_error(request, exception=None, status=500):
    return HttpResponse("Request could not be completed.", status=status, content_type="text/plain")
