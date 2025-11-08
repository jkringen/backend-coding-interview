from typing import Optional, Tuple
import os

from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.backends import TokenBackend

EXTERNAL_PUBLIC_KEY = os.environ.get("API_JWT_PUBLIC_KEY")
EXTERNAL_ISSUER = "frontend.photos"
EXTERNAL_AUDIENCE = "backend.photos"


class LocalJWTAuthentication(JWTAuthentication):
    """Validates tokens we issue via /api/token/ using SIMPLE_JWT settings."""

    pass


class ExternalJWTAuthentication(BaseAuthentication):
    """
    Validates third-party JWTs provided via frontend signed into external service.
    If validation fails, return None so DRF can try the next backend.
    """

    token_backend = TokenBackend(
        algorithm="RS256",
        signing_key=None,
        verifying_key=EXTERNAL_PUBLIC_KEY,
        audience=EXTERNAL_AUDIENCE,
        issuer=EXTERNAL_ISSUER,
        leeway=30,
    )

    def authenticate(self, request) -> Optional[Tuple[object, None]]:
        # make sure we have an auth header
        auth = get_authorization_header(request).decode("utf-8")
        if not auth.startswith("Bearer "):
            return None

        # attempt to decode the token
        raw = auth.split(" ", 1)[1]
        try:
            claims = self.token_backend.decode(raw, verify=True)
        except Exception:
            # Not a valid external token; let the next backend try (e.g., LocalJWTAuthentication).
            return None

        # Map external identity to a Django user
        sub = claims.get("sub") or claims.get("user_id") or claims.get("uid")
        if not sub:
            raise exceptions.AuthenticationFailed("Missing subject claim")

        # ensure parity with User table
        email = claims.get("email")
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username=f"ext:{sub}",
            defaults={"email": email or "", "is_active": True},
        )
        return (user, None)
