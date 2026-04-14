from django.core.management.base import BaseCommand

from apps.unidades.models import Fabrica, UnidadeProdutiva


FABRICAS_E_UNIDADES = (
    {
        "name": "Araxa",
        "code": "ARAXA",
        "unidades": (
            {"name": "Linha 1", "code": "L1"},
            {"name": "Linha 2", "code": "L2"},
            {"name": "Flocos", "code": "FLOCOS"},
        ),
    },
    {
        "name": "Perdizes",
        "code": "PERDIZES",
        "unidades": (
            {"name": "Linha 3", "code": "L3"},
            {"name": "Linha 4", "code": "L4"},
        ),
    },
)


class Command(BaseCommand):
    help = "Cria fabricas e unidades produtivas padrao do sistema."

    def handle(self, *args, **options):
        for fabrica_data in FABRICAS_E_UNIDADES:
            fabrica, _ = Fabrica.objects.get_or_create(
                code=fabrica_data["code"],
                defaults={
                    "name": fabrica_data["name"],
                    "is_active": True,
                },
            )
            if not fabrica.is_active:
                fabrica.is_active = True
                fabrica.save(update_fields=["is_active", "updated_at"])

            for unidade_data in fabrica_data["unidades"]:
                unidade, _ = UnidadeProdutiva.objects.get_or_create(
                    fabrica=fabrica,
                    code=unidade_data["code"],
                    defaults={
                        "name": unidade_data["name"],
                        "is_active": True,
                    },
                )
                if not unidade.is_active:
                    unidade.is_active = True
                    unidade.save(update_fields=["is_active", "updated_at"])

        self.stdout.write(self.style.SUCCESS("Fabricas e unidades produtivas sincronizadas com sucesso."))
