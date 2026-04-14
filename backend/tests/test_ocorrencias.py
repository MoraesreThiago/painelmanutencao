from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.access.models import Role, UserArea
from apps.accounts.models import User
from apps.colaboradores.models import Collaborator
from apps.equipamentos.models import Equipment
from apps.ocorrencias.models import Occurrence
from apps.unidades.models import Area, Fabrica, Location, UnidadeProdutiva
from common.enums import (
    AreaCode,
    EquipmentStatus,
    EquipmentType,
    OccurrenceClassification,
    OccurrenceStatus,
    RecordStatus,
    RoleName,
)


class OccurrenceModuleTests(TestCase):
    def setUp(self):
        self.area_eletrica = Area.objects.create(name="Eletrica", code=AreaCode.ELETRICA)
        self.area_mecanica = Area.objects.create(name="Mecanica", code=AreaCode.MECANICA)
        self.fabrica_araxa = Fabrica.objects.create(name="Araxa", code="ARAXA", is_active=True)
        self.fabrica_perdizes = Fabrica.objects.create(name="Perdizes", code="PERDIZES", is_active=True)
        self.unidade_l1 = UnidadeProdutiva.objects.create(fabrica=self.fabrica_araxa, name="Linha 1", code="L1")
        self.unidade_l4 = UnidadeProdutiva.objects.create(fabrica=self.fabrica_perdizes, name="Linha 4", code="L4")
        self.location_eletrica = Location.objects.create(
            name="Sala eletrica",
            sector="Utilidades",
            area=self.area_eletrica,
            unidade=self.unidade_l1,
        )
        self.location_mecanica = Location.objects.create(
            name="Oficina",
            sector="Planta",
            area=self.area_mecanica,
            unidade=self.unidade_l4,
        )

        self.role_manutentor = Role.objects.create(name=RoleName.MANUTENTOR)
        self.role_lider = Role.objects.create(name=RoleName.LIDER)

        self.operational_user = User.objects.create_user(
            email="eletrica.n1@maintenance.example.com",
            password="Teste@123",
            full_name="Manutentor Eletrica N1",
            area=self.area_eletrica,
            role=self.role_manutentor,
            unidade=self.unidade_l1,
            is_active=True,
        )
        self.leader_user = User.objects.create_user(
            email="eletrica.lider@maintenance.example.com",
            password="Teste@123",
            full_name="Lider Eletrica",
            area=self.area_eletrica,
            role=self.role_lider,
            unidade=self.unidade_l1,
            is_active=True,
        )
        UserArea.objects.create(user=self.operational_user, area=self.area_eletrica)
        UserArea.objects.create(user=self.leader_user, area=self.area_eletrica)

        self.collaborator = Collaborator.objects.create(
            full_name="Carlos Silva",
            registration_number="COL-001",
            job_title="Tecnico",
            status=RecordStatus.ACTIVE,
            area=self.area_eletrica,
        )

        self.equipment_eletrica = Equipment.objects.create(
            code="EQ-100",
            tag="TAG-100",
            description="Painel de comando",
            sector="Utilidades",
            type=EquipmentType.GENERIC,
            status=EquipmentStatus.ACTIVE,
            registered_at=timezone.now(),
            area=self.area_eletrica,
            unidade=self.unidade_l1,
            location=self.location_eletrica,
        )
        self.equipment_mecanica = Equipment.objects.create(
            code="EQ-200",
            tag="TAG-200",
            description="Bomba de processo",
            sector="Planta",
            type=EquipmentType.GENERIC,
            status=EquipmentStatus.ACTIVE,
            registered_at=timezone.now(),
            area=self.area_mecanica,
            unidade=self.unidade_l4,
            location=self.location_mecanica,
        )

        self.occurrence_eletrica = Occurrence.objects.create(
            equipment=self.equipment_eletrica,
            area=self.area_eletrica,
            location=self.location_eletrica,
            unidade=self.unidade_l1,
            responsible_collaborator=self.collaborator,
            reported_by_user=self.operational_user,
            classification=OccurrenceClassification.FAILURE,
            status=OccurrenceStatus.OPEN,
            occurred_at=timezone.now(),
            description="Falha intermitente no painel principal.",
            had_downtime=True,
            downtime_minutes=15,
        )
        self.occurrence_mecanica = Occurrence.objects.create(
            equipment=self.equipment_mecanica,
            area=self.area_mecanica,
            location=self.location_mecanica,
            unidade=self.unidade_l4,
            classification=OccurrenceClassification.ANOMALY,
            status=OccurrenceStatus.OPEN,
            occurred_at=timezone.now(),
            description="Vazamento identificado na linha da bomba.",
            had_downtime=False,
        )

        self.client = Client()
        self.api_client = APIClient()

    def test_occurrence_list_is_scoped_to_user_area(self):
        self.client.force_login(self.operational_user)
        response = self.client.get(reverse("ocorrencias:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EQ-100")
        self.assertNotContains(response, "EQ-200")

    def test_occurrence_list_htmx_returns_partial(self):
        self.client.force_login(self.operational_user)
        response = self.client.get(
            reverse("ocorrencias:list"),
            {"search": "Painel"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ocorrencias registradas")
        self.assertNotContains(response, "<!doctype html>", html=False)

    def test_operational_user_can_create_occurrence_and_equipment_detail_shows_it(self):
        self.client.force_login(self.operational_user)
        response = self.client.post(
            reverse("ocorrencias:create"),
            {
                "area": str(self.area_eletrica.id),
                "equipment": str(self.equipment_eletrica.id),
                "location": str(self.location_eletrica.id),
                "classification": OccurrenceClassification.INSPECTION,
                "responsible_collaborator": str(self.collaborator.id),
                "occurred_at": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "had_downtime": "",
                "downtime_minutes": "",
                "description": "Inspecao registrada apos ajuste fino.",
                "notes": "Sem impacto operacional relevante.",
            },
        )

        self.assertEqual(response.status_code, 302)
        created = Occurrence.objects.get(description__icontains="Inspecao registrada")
        equipment_detail = self.client.get(reverse("equipamentos:detail", kwargs={"pk": self.equipment_eletrica.pk}))

        self.assertContains(equipment_detail, created.description)

    def test_status_update_changes_equipment_status_and_registers_timeline(self):
        self.client.force_login(self.operational_user)
        self.equipment_eletrica.refresh_from_db()
        self.assertEqual(self.equipment_eletrica.status, EquipmentStatus.ACTIVE)

        status_response = self.client.post(
            reverse("ocorrencias:update-status", kwargs={"pk": self.occurrence_eletrica.pk}),
            {"status": OccurrenceStatus.IN_PROGRESS, "note": "Equipe em atendimento."},
        )

        self.assertEqual(status_response.status_code, 302)
        self.equipment_eletrica.refresh_from_db()
        self.occurrence_eletrica.refresh_from_db()
        self.assertEqual(self.equipment_eletrica.status, EquipmentStatus.UNDER_MAINTENANCE)

        resolve_response = self.client.post(
            reverse("ocorrencias:update-status", kwargs={"pk": self.occurrence_eletrica.pk}),
            {"status": OccurrenceStatus.RESOLVED, "note": "Falha eliminada."},
        )

        self.assertEqual(resolve_response.status_code, 302)
        self.equipment_eletrica.refresh_from_db()
        self.occurrence_eletrica.refresh_from_db()
        self.assertEqual(self.equipment_eletrica.status, EquipmentStatus.ACTIVE)
        self.assertEqual(self.occurrence_eletrica.status, OccurrenceStatus.RESOLVED)
        self.assertIsNotNone(self.occurrence_eletrica.resolved_at)

        detail_response = self.client.get(reverse("ocorrencias:detail", kwargs={"pk": self.occurrence_eletrica.pk}))
        self.assertContains(detail_response, "Status da ocorrencia do equipamento EQ-100 alterado")

    def test_history_page_lists_occurrence_events(self):
        self.client.force_login(self.operational_user)
        self.client.post(
            reverse("ocorrencias:update-status", kwargs={"pk": self.occurrence_eletrica.pk}),
            {"status": OccurrenceStatus.IN_PROGRESS, "note": "Fila de manutencao."},
        )

        response = self.client.get(reverse("ocorrencias:history"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EQ-100")

    def test_occurrence_api_is_paginated_and_scoped(self):
        self.api_client.force_authenticate(user=self.operational_user)
        response = self.api_client.get(reverse("api-ocorrencias"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["equipment_code"], "EQ-100")

    def test_user_cannot_access_occurrence_from_other_area_via_web_or_api(self):
        self.client.force_login(self.operational_user)
        web_response = self.client.get(reverse("ocorrencias:detail", kwargs={"pk": self.occurrence_mecanica.pk}))
        self.assertEqual(web_response.status_code, 403)

        self.api_client.force_authenticate(user=self.operational_user)
        api_response = self.api_client.get(reverse("api-ocorrencia-detail", kwargs={"pk": self.occurrence_mecanica.pk}))
        self.assertEqual(api_response.status_code, 403)

    def test_operational_user_can_create_and_update_status_via_api(self):
        self.api_client.force_authenticate(user=self.operational_user)
        create_response = self.api_client.post(
            reverse("api-ocorrencias"),
            {
                "equipment": str(self.equipment_eletrica.id),
                "area": str(self.area_eletrica.id),
                "location": str(self.location_eletrica.id),
                "classification": OccurrenceClassification.FAILURE,
                "description": "Falha registrada via API.",
                "had_downtime": True,
                "downtime_minutes": 22,
                "responsible_collaborator": str(self.collaborator.id),
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, 201)
        occurrence_id = create_response.data["id"]
        status_response = self.api_client.post(
            reverse("api-ocorrencia-status", kwargs={"pk": occurrence_id}),
            {"status": OccurrenceStatus.RESOLVED, "note": "Resolucao remota."},
            format="json",
        )

        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.data["status"], OccurrenceStatus.RESOLVED)

    def test_dashboard_api_rejects_area_without_permission(self):
        self.api_client.force_authenticate(user=self.operational_user)
        response = self.api_client.get(reverse("api-dashboard"), {"area": self.area_mecanica.code})
        self.assertEqual(response.status_code, 403)
