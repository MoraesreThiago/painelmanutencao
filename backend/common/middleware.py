from __future__ import annotations

from common.permissions import ASSUMABLE_ROLE_NAMES, PermissionName, has_actual_permission, normalize_role_name


ASSUMED_ROLE_SESSION_KEY = "sgm_assumed_role_name"


class AssumedContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            assumed_role_name = normalize_role_name(request.session.get(ASSUMED_ROLE_SESSION_KEY))
            if has_actual_permission(user, PermissionName.ASSUME_AREA_CONTEXT) and assumed_role_name in ASSUMABLE_ROLE_NAMES:
                user._assumed_role_name = assumed_role_name
            else:
                request.session.pop(ASSUMED_ROLE_SESSION_KEY, None)
                if hasattr(user, "_assumed_role_name"):
                    delattr(user, "_assumed_role_name")
        return self.get_response(request)
