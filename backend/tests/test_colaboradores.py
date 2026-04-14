from django.test import Client, TestCase
from django.urls import reverse

from apps.access.models import Role, UserArea
from apps.accounts.models import User
from apps.colaboradores.models import Collaborator
from apps.unidades.models import Area, Fabrica, UnidadeProdutiva
from common.enums import AreaCode, RecordStatus, RoleName


class TeamManagementModuleTests(TestCase):
    def setUp(self):
        self.area_eletrica = Area.objects.create(name="Eletrica", code=AreaCode.ELETRICA)
        self.area_mecanica = Area.objects.create(name="Mecanica", code=AreaCode.MECANICA)
        self.fabrica_araxa = Fabrica.objects.create(name="Araxa", code="ARAXA", is_active=True)
        self.fabrica_perdizes = Fabrica.objects.create(name="Perdizes", code="PERDIZES", is_active=True)
        self.unidade_l1 = UnidadeProdutiva.objects.create(fabrica=self.fabrica_araxa, name="Linha 1", code="L1")
        self.unidade_l4 = UnidadeProdutiva.objects.create(fabrica=self.fabrica_perdizes, name="Linha 4", code="L4")

        self.role_manutentor = Role.objects.create(name=RoleName.MANUTENTOR)
        self.role_inspetor = Role.objects.create(name=RoleName.INSPETOR)
        self.role_lider = Role.objects.create(name=RoleName.LIDER)
        self.role_supervisor = Role.objects.create(name=RoleName.SUPERVISOR)
        self.role_admin = Role.objects.create(name=RoleName.ADMIN)

        self.maintenance_user = User.objects.create_user(
            email="manutentor.eletrica@maintenance.example.com",
            password="Teste@123",
            full_name="Manutentor Eletrica",
            area=self.area_eletrica,
            role=self.role_manutentor,
            is_active=True,
        )
        self.leader_user = User.objects.create_user(
            email="lider.eletrica@maintenance.example.com",
            password="Teste@123",
            full_name="Lider Eletrica",
            area=self.area_eletrica,
            fabrica=self.fabrica_araxa,
            unidade=self.unidade_l1,
            role=self.role_lider,
            is_active=True,
        )
        self.inspector_user = User.objects.create_user(
            email="inspetor.eletrica@maintenance.example.com",
            password="Teste@123",
            full_name="Inspetor Eletrica",
            area=self.area_eletrica,
            role=self.role_inspetor,
            is_active=True,
        )
        self.supervisor_user = User.objects.create_user(
            email="supervisor.mecanica@maintenance.example.com",
            password="Teste@123",
            full_name="Supervisor Mecanica",
            area=self.area_mecanica,
            role=self.role_supervisor,
            is_active=True,
        )
        self.admin_user = User.objects.create_user(
            email="admin@maintenance.example.com",
            password="Teste@123",
            full_name="Administrador do Sistema",
            area=self.area_eletrica,
            fabrica=self.fabrica_araxa,
            role=self.role_admin,
            is_active=True,
        )

        UserArea.objects.create(user=self.maintenance_user, area=self.area_eletrica)
        UserArea.objects.create(user=self.inspector_user, area=self.area_eletrica)
        UserArea.objects.create(user=self.leader_user, area=self.area_eletrica)
        UserArea.objects.create(user=self.supervisor_user, area=self.area_mecanica)
        UserArea.objects.create(user=self.admin_user, area=self.area_eletrica)
        UserArea.objects.create(user=self.admin_user, area=self.area_mecanica)

        self.linked_user = User.objects.create_user(
            email="tecnico.eletrica@maintenance.example.com",
            password="Teste@123",
            full_name="Tecnico da Eletrica",
            area=self.area_eletrica,
            fabrica=self.fabrica_araxa,
            unidade=self.unidade_l1,
            role=self.role_manutentor,
            is_active=True,
        )
        UserArea.objects.create(user=self.linked_user, area=self.area_eletrica)

        Collaborator.objects.create(
            full_name="Carlos Eletrica",
            registration_number="MAT-100",
            job_title="Eletricista",
            contact_phone="(31) 99999-0001",
            status=RecordStatus.ACTIVE,
            area=self.area_eletrica,
            linked_user=self.linked_user,
        )
        Collaborator.objects.create(
            full_name="Ana Planejamento",
            registration_number="MAT-101",
            job_title="Planejadora",
            contact_phone="(31) 99999-0002",
            status=RecordStatus.INACTIVE,
            area=self.area_eletrica,
        )
        Collaborator.objects.create(
            full_name="Bruno Mecanica",
            registration_number="MAT-200",
            job_title="Mecanico",
            contact_phone="(31) 99999-0003",
            status=RecordStatus.ACTIVE,
            area=self.area_mecanica,
        )

        self.client = Client()

    def test_team_management_requires_leadership_permission(self):
        self.client.force_login(self.maintenance_user)

        response = self.client.get(reverse("colaboradores:team"))

        self.assertEqual(response.status_code, 403)

    def test_team_management_is_not_available_for_inspetor(self):
        self.client.force_login(self.inspector_user)

        response = self.client.get(reverse("colaboradores:team"))

        self.assertEqual(response.status_code, 403)

    def test_team_management_is_not_available_for_supervisor(self):
        self.client.force_login(self.supervisor_user)

        response = self.client.get(reverse("colaboradores:team"), {"area": AreaCode.MECANICA})

        self.assertEqual(response.status_code, 403)

    def test_leader_can_view_team_management_scoped_to_current_area(self):
        self.client.force_login(self.leader_user)

        response = self.client.get(reverse("colaboradores:team"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestao da equipe")
        self.assertContains(response, "Carlos Eletrica")
        self.assertContains(response, "Ana Planejamento")
        self.assertNotContains(response, "Bruno Mecanica")
        self.assertContains(response, "/equipe/?area=ELETRICA", html=False)
        self.assertContains(response, "Linha 1")
        self.assertContains(response, "Araxa")

    def test_team_management_filters_by_text_and_status(self):
        self.client.force_login(self.leader_user)

        response = self.client.get(
            reverse("colaboradores:team"),
            {
                "search": "Carlos",
                "status": RecordStatus.ACTIVE,
            },
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Carlos Eletrica")
        self.assertNotContains(response, "Ana Planejamento")
        self.assertNotContains(response, "<!doctype html>", html=False)

    def test_team_management_filters_by_fabrica_and_unidade(self):
        linked_user_perdizes = User.objects.create_user(
            email="tecnico.perdizes@maintenance.example.com",
            password="Teste@123",
            full_name="Tecnico Perdizes",
            area=self.area_eletrica,
            fabrica=self.fabrica_perdizes,
            unidade=self.unidade_l4,
            role=self.role_manutentor,
            is_active=True,
        )
        UserArea.objects.create(user=linked_user_perdizes, area=self.area_eletrica)
        Collaborator.objects.create(
            full_name="Carlos Perdizes",
            registration_number="MAT-300",
            job_title="Eletricista",
            contact_phone="(31) 99999-0004",
            status=RecordStatus.ACTIVE,
            area=self.area_eletrica,
            linked_user=linked_user_perdizes,
        )

        self.client.force_login(self.leader_user)

        response = self.client.get(
            reverse("colaboradores:team"),
            {
                "fabrica": "ARAXA",
                "unidade": str(self.unidade_l1.id),
            },
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Carlos Eletrica")
        self.assertNotContains(response, "Carlos Perdizes")

    def test_admin_cannot_open_team_management_without_leader_context(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("colaboradores:team"), {"area": AreaCode.MECANICA})

        self.assertEqual(response.status_code, 403)
