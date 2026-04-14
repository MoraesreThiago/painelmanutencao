from django.conf import settings
from django.core.management.base import BaseCommand

from apps.access.models import Role, UserArea
from apps.accounts.models import User
from apps.unidades.models import Area
from common.enums import AreaCode, RoleName


class Command(BaseCommand):
    help = "Cria áreas, papéis e usuário administrador padrão."

    def handle(self, *args, **options):
        area_defaults = [
            (AreaCode.ELETRICA, "Elétrica"),
            (AreaCode.MECANICA, "Mecânica"),
            (AreaCode.INSTRUMENTACAO, "Instrumentação"),
        ]
        areas = {}
        for code, name in area_defaults:
            area, _ = Area.objects.get_or_create(code=code, defaults={"name": name})
            areas[code] = area

        for role_name in RoleName.values:
            Role.objects.get_or_create(name=role_name)

        admin_role = Role.objects.get(name=RoleName.ADMIN)
        admin_user, created = User.objects.get_or_create(
            email=settings.DEFAULT_ADMIN_EMAIL,
            defaults={
                "full_name": "Administrador do Sistema",
                "role": admin_role,
                "area": areas[AreaCode.ELETRICA],
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            admin_user.set_password(settings.DEFAULT_ADMIN_PASSWORD)
            admin_user.save()

        for area in areas.values():
            UserArea.objects.get_or_create(user=admin_user, area=area)

        self.stdout.write(self.style.SUCCESS("Bootstrap inicial concluído."))
