from django.test import Client, TestCase
from django.urls import reverse

from apps.access.models import Role, UserArea
from apps.accounts.models import User
from apps.unidades.models import Area
from common.middleware import ASSUMED_ROLE_SESSION_KEY
from common.enums import AreaCode, RoleName


class DjangoMonolithSmokeTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(name="Eletrica", code=AreaCode.ELETRICA)
        self.role = Role.objects.create(name=RoleName.MANUTENTOR)
        self.user = User.objects.create_user(
            email="eletrica.n1@maintenance.example.com",
            password="Teste@123",
            full_name="Manutentor Eletrica N1",
            area=self.area,
            role=self.role,
            is_active=True,
        )
        UserArea.objects.create(user=self.user, area=self.area)
        self.client = Client()

    def test_home_redirects_to_login(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("accounts:login"))

    def test_login_redirects_to_area_dashboard_with_current_area(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"email": self.user.email, "password": "Teste@123", "remember_me": True},
        )
        self.assertRedirects(response, f'{reverse("access:area-dashboard")}?area=ELETRICA')

    def test_workspace_respects_sidebar_cookie_state_and_accessibility_markup(self):
        self.client.force_login(self.user)
        self.client.cookies["sgm_sidebar_collapsed"] = "true"

        response = self.client.get(reverse("access:workspace-eletrica"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="app-shell is-sidebar-collapsed"', html=False)
        self.assertContains(response, 'aria-controls="app-sidebar"', html=False)
        self.assertContains(response, 'data-sidebar-tooltip="Painel Principal"', html=False)
        self.assertContains(response, 'aria-current="page"', html=False)

    def test_area_dashboard_uses_area_query_context(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("access:area-dashboard"), {"area": AreaCode.ELETRICA})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dashboard_area"].code, AreaCode.ELETRICA)
        self.assertContains(response, '?area=ELETRICA', html=False)

    def test_legacy_dashboard_route_redirects_to_area_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("access:dashboard"))

        self.assertRedirects(response, f'{reverse("access:area-dashboard")}?area=ELETRICA')

    def test_energy_monitoring_page_is_available_and_exposed_in_sidebar(self):
        self.client.force_login(self.user)

        workspace_response = self.client.get(reverse("access:workspace-eletrica"))
        page_response = self.client.get(reverse("access:power-monitoring"), {"area": AreaCode.ELETRICA})

        self.assertEqual(page_response.status_code, 200)
        self.assertContains(workspace_response, "Principal")
        self.assertContains(workspace_response, "Ativos")
        self.assertContains(workspace_response, "Energia")
        self.assertContains(workspace_response, "Assistente")
        self.assertContains(workspace_response, "/ordens-servico/?area=ELETRICA", html=False)
        self.assertContains(workspace_response, "/equipamentos/?area=ELETRICA", html=False)
        self.assertContains(workspace_response, "/motores-eletricos/?area=ELETRICA", html=False)
        self.assertContains(workspace_response, "/assistente/chat/?area=ELETRICA", html=False)
        self.assertContains(
            workspace_response,
            "/energia/tensao-corrente-geracao/?area=ELETRICA",
            html=False,
        )
        self.assertContains(page_response, "Fase R")
        self.assertContains(page_response, "Fase S")
        self.assertContains(page_response, "Fase T")
        self.assertContains(page_response, '?area=ELETRICA', html=False)

    def test_dashboard_api_requires_authentication(self):
        response = self.client.get("/api/v1/dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_logout_requires_post(self):
        self.client.force_login(self.user)

        get_response = self.client.get(reverse("accounts:logout"))
        post_response = self.client.post(reverse("accounts:logout"))

        self.assertEqual(get_response.status_code, 405)
        self.assertRedirects(post_response, reverse("accounts:login"))

    def test_monthly_summary_requires_report_permission(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("access:monthly-summary"))
        self.assertEqual(response.status_code, 403)


class MonthlySummaryAccessTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(name="Eletrica", code=AreaCode.ELETRICA)
        self.role = Role.objects.create(name=RoleName.LIDER)
        self.user = User.objects.create_user(
            email="lider.eletrica@maintenance.example.com",
            password="Teste@123",
            full_name="Lider Eletrica",
            area=self.area,
            role=self.role,
            is_active=True,
        )
        UserArea.objects.create(user=self.user, area=self.area)
        self.client = Client()

    def test_monthly_summary_is_available_for_user_with_report_permission(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("access:monthly-summary"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resumo Mensal")


class MechanicalSidebarVisibilityTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(name="Mecanica", code=AreaCode.MECANICA)
        self.role = Role.objects.create(name=RoleName.MANUTENTOR)
        self.user = User.objects.create_user(
            email="mecanica.n1@maintenance.example.com",
            password="Teste@123",
            full_name="Manutentor Mecanica N1",
            area=self.area,
            role=self.role,
            is_active=True,
        )
        UserArea.objects.create(user=self.user, area=self.area)
        self.client = Client()

    def test_mechanical_workspace_hides_electrical_only_modules(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("access:workspace-mecanica"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ativos")
        self.assertContains(response, "Equipamentos")
        self.assertNotContains(response, "/motores-eletricos/")
        self.assertNotContains(response, reverse("access:power-monitoring"))

    def test_mechanical_user_cannot_open_energy_monitoring(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("access:power-monitoring"))

        self.assertEqual(response.status_code, 403)


class AdminAreaContextSwitchTests(TestCase):
    def setUp(self):
        self.area_eletrica = Area.objects.create(name="Eletrica", code=AreaCode.ELETRICA)
        self.area_mecanica = Area.objects.create(name="Mecanica", code=AreaCode.MECANICA)
        self.area_instrumentacao = Area.objects.create(name="Instrumentacao", code=AreaCode.INSTRUMENTACAO)
        self.role = Role.objects.create(name=RoleName.ADMIN)
        self.user = User.objects.create_user(
            email="admin@maintenance.example.com",
            password="Teste@123",
            full_name="Administrador Global",
            area=self.area_eletrica,
            role=self.role,
            is_active=True,
        )
        UserArea.objects.create(user=self.user, area=self.area_eletrica)
        UserArea.objects.create(user=self.user, area=self.area_mecanica)
        UserArea.objects.create(user=self.user, area=self.area_instrumentacao)
        self.client = Client()

    def test_admin_sees_context_switch_form_in_profile_menu(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("access:workspace-eletrica"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alterar contexto")
        self.assertContains(response, 'name="area"', html=False)
        self.assertContains(response, 'name="role_name"', html=False)
        self.assertContains(response, reverse("access:context-switch"), html=False)
        self.assertContains(response, "Eletrica")
        self.assertContains(response, "Mecanica")
        self.assertContains(response, "Instrumentacao")

    def test_admin_can_apply_context_and_sidebar_uses_effective_role(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("access:context-switch"),
            {
                "area": AreaCode.MECANICA,
                "role_name": RoleName.MANUTENTOR,
            },
        )

        self.assertRedirects(response, f'{reverse("access:area-dashboard")}?area=MECANICA')
        self.assertEqual(self.client.session[ASSUMED_ROLE_SESSION_KEY], RoleName.MANUTENTOR)

        response = self.client.get(reverse("access:area-dashboard"), {"area": AreaCode.MECANICA})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Voltar para Admin")
        self.assertContains(response, 'option value="MANUTENTOR" selected', html=False)
        self.assertContains(response, reverse("access:context-reset"), html=False)
        self.assertNotContains(response, "Resumo Mensal")
        self.assertNotContains(response, "/motores-eletricos/")
        self.assertNotContains(response, reverse("access:power-monitoring"))

    def test_admin_can_reset_assumed_context(self):
        self.client.force_login(self.user)
        session = self.client.session
        session[ASSUMED_ROLE_SESSION_KEY] = RoleName.MANUTENTOR
        session.save()

        response = self.client.post(
            reverse("access:context-reset"),
            {
                "area": AreaCode.ELETRICA,
            },
        )

        self.assertRedirects(response, f'{reverse("access:area-dashboard")}?area=ELETRICA')

        response = self.client.get(reverse("access:area-dashboard"), {"area": AreaCode.ELETRICA})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Voltar para Admin")
        self.assertContains(response, "Resumo Mensal")
        self.assertContains(response, "/motores-eletricos/?area=ELETRICA", html=False)

    def test_admin_mechanical_workspace_keeps_mechanical_context_in_sidebar(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("access:workspace-mecanica"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/painelprincipal/?area=MECANICA"', html=False)
        self.assertContains(response, "Mecanica")
        self.assertNotContains(response, "/motores-eletricos/")
        self.assertNotContains(response, reverse("access:power-monitoring"))

    def test_admin_can_assume_inspetor_context_without_becoming_lider(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("access:context-switch"),
            {
                "area": AreaCode.ELETRICA,
                "role_name": RoleName.INSPETOR,
            },
        )

        self.assertRedirects(response, f'{reverse("access:area-dashboard")}?area=ELETRICA')
        self.assertEqual(self.client.session[ASSUMED_ROLE_SESSION_KEY], RoleName.INSPETOR)

        response = self.client.get(reverse("access:area-dashboard"), {"area": AreaCode.ELETRICA})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'option value="INSPETOR" selected', html=False)
        self.assertNotContains(response, "/equipe/?area=ELETRICA", html=False)
