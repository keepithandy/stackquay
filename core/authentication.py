import hashlib

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import AccessToken


class BearerAuthentication(BaseAuthentication):
    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if len(parts) != 2 or parts[0].lower() != b"bearer" or len(parts[1]) > 256:
            raise AuthenticationFailed("Use Authorization: Bearer <token>.")
        digest = hashlib.sha256(parts[1]).hexdigest()
        token = AccessToken.objects.select_related("user").filter(digest=digest).first()
        if not token or token.expires_at <= timezone.now() or not token.user.is_active:
            raise AuthenticationFailed("Invalid or expired token.")
        return token.user, token

    def authenticate_header(self, request):
        return "Bearer"
