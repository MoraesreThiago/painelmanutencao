from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.access.models import Role, UserArea
from apps.accounts.models import User
from apps.equipamentos.models import Equipment
from apps.unidades.models import Area, Fabrica, Location, UnidadeProdutiva
from common.enums import AreaCode, EquipmentStatus, EquipmentType, RoleName


class EquipmentModuleTests(TestCase):
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
        self.equipment_eletrica_aux = Equipment.objects.create(
            code="EQ-101",
            tag="TAG-EXAUSTOR",
            description="Motor do exaustor",
            sector="Utilidades",
            type=EquipmentType.MOTOR,
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

        self.client = Client()
        self.api_client = APIClient()

    def test_equipment_list_is_scoped_to_user_area_and_unidade(self):
        self.client.force_login(self.operational_user)
        response = self.client.get(reverse("equipamentos:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EQ-100")
        self.assertContains(response, "EQ-101")
        self.assertNotContains(response, "EQ-200")

    def test_equipment_list_htmx_returns_partial(self):
        self.client.force_login(self.operational_user)
        response = self.client.get(
            reverse("equipamentos:list"),
            {"equipment_name": "Painel"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Equipamentos")
        self.assertContains(response, "Painel de comando")
        self.assertNotContains(response, "<!doctype html>", html=False)

    def test_equipment_list_filters_partially_by_equipment_name(self):
        self.client.force_login(self.operational_user)
        response = self.client.get(reverse("equipamentos:list"), {"equipment_name": "exaust"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EQ-101")
        self.assertContains(response, "Motor do exaustor")
        self.assertNotContains(response, "EQ-100")

    def test_equipment_list_filters_partially_by_tag_name(self):
        self.client.force_login(self.operational_user)
        response = self.client.get(reverse("equipamentos:list"), {"tag_name": "exaust"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EQ-101")
        self.assertContains(response, "TAG-EXAUSTOR")
        self.assertNotContains(response, "EQ-100")

    def test_equipment_list_can_filter_by_fabrica_and_unidade(self):
        self.client.force_login(self.leader_user)
        response = self.client.get(
            reverse("equipamentos:list"),
            {"fabrica": self.fabrica_araxa.code, "unidade": str(self.unidade_l1.id)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EQ-100")
        self.assertNotContains(response, "EQ-200")

    def test_operational_user_cannot_create_equipment(self):
        self.client.force_login(self.operational_user)
        response = self.client.get(reverse("equipamentos:create"))
        self.assertEqual(response.status_code, 403)

    def test_leader_can_create_and_toggle_equipment(self):
        self.client.force_login(self.leader_user)
        response = self.client.post(
            reverse("equipamentos:create"),
            {
                "code": "EQ-300",
                "tag": "TAG-300",
                "description": "Motor auxiliar",
                "sector": "Utilidades",
                "manufacturer": "WEG",
                "model": "W22",
                "serial_number": "SN-300",
                "type": EquipmentType.MOTOR,
                "status": EquipmentStatus.ACTIVE,
                "registered_at": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "area": str(self.area_eletrica.id),
                "unidade": str(self.unidade_l1.id),
                "location": str(self.location_eletrica.id),
                "notes": "Cadastro inicial",
            },
        )

        self.assertEqual(response.status_code, 302)
        created = Equipment.objects.get(code="EQ-300")
        toggle_response = self.client.post(reverse("equipamentos:toggle-status", kwargs={"pk": created.pk}))
        created.refresh_from_db()

        self.assertEqual(toggle_response.status_code, 302)
        self.assertEqual(created.status, EquipmentStatus.INACTIVE)

    def test_equipment_api_is_paginated_and_scoped(self):
        self.api_client.force_authenticate(user=self.operational_user)
        response = self.api_client.get(reverse("api-equipamentos"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["code"], "EQ-100")
        self.assertEqual(response.data["results"][0]["unidade_name"], "Linha 1")

    def test_leader_can_create_equipment_via_api(self):
        self.api_client.force_authenticate(user=self.leader_user)
        response = self.api_client.post(
            reverse("api-equipamentos"),
            {
                "code": "EQ-400",
                "tag": "TAG-400",
                "description": "Instrumento reserva",
                "sector": "Utilidades",
                "manufacturer": "Siemens",
                "model": "X1",
                "serial_number": "SN-400",
                "type": EquipmentType.INSTRUMENT,
                "status": EquipmentStatus.ACTIVE,
                "area": str(self.area_eletrica.id),
                "unidade": str(self.unidade_l1.id),
                "location": str(self.location_eletrica.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Equipment.objects.filter(code="EQ-400").exists())
