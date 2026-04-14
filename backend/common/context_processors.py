import time

from django.conf import settings


def app_shell(request):
    return {
        "APP_NAME": settings.APP_NAME,
        "APP_SUBTITLE": settings.APP_SUBTITLE,
        "DEBUG": settings.DEBUG,
        "STATIC_DEV_VERSION": str(int(time.time())) if settings.DEBUG else "",
    }
