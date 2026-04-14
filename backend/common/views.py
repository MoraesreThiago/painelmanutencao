from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.http import FileResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views import View

from common.permissions import resolve_post_login_url


class HomeRedirectView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(resolve_post_login_url(request.user))
        return HttpResponseRedirect(reverse("accounts:login"))


class OfflineView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return TemplateResponse(request, "common/offline.html", {})


class ManifestView(View):
    def get(self, request, *args, **kwargs):
        return TemplateResponse(
            request,
            "common/manifest.webmanifest",
            {"app_name": settings.APP_NAME, "app_subtitle": settings.APP_SUBTITLE},
            content_type="application/manifest+json",
        )


class ServiceWorkerView(View):
    def get(self, request, *args, **kwargs):
        return TemplateResponse(
            request,
            "common/sw.js",
            {},
            content_type="application/javascript",
        )


class LogoAssetView(View):
    def get(self, request, *args, **kwargs):
        logo_path = Path(settings.BASE_DIR) / "static" / "images" / "sgm-logo-clean.png"
        if not logo_path.exists():
            raise Http404("Logo nao encontrada.")
        return FileResponse(logo_path.open("rb"), content_type="image/png")
