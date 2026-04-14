from __future__ import annotations

from django.contrib.auth import authenticate
from django.utils import timezone

from common.permissions import resolve_post_login_url


def authenticate_user(*, request, email: str, password: str):
    user = authenticate(request=request, email=email, password=password)
    if not user:
        return None
    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at"])
    return user


def login_redirect_for(user) -> str:
    return resolve_post_login_url(user)
