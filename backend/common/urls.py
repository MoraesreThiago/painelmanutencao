from django.urls import path

from common.views import HomeRedirectView, LogoAssetView, ManifestView, OfflineView, ServiceWorkerView


urlpatterns = [
    path("", HomeRedirectView.as_view(), name="home"),
    path("offline/", OfflineView.as_view(), name="offline"),
    path("manifest.webmanifest", ManifestView.as_view(), name="manifest"),
    path("sw.js", ServiceWorkerView.as_view(), name="service-worker"),
    path("branding/app-logo.png", LogoAssetView.as_view(), name="brand-logo"),
]
