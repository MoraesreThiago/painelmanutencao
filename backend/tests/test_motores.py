from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.access.models import Role, UserArea
from apps.accounts.models import User
from apps.motores.models import BurnedMotorCase, ElectricMotor
from apps.unidades.models import Area, Fabrica, UnidadeProdutiva
from common.enums import AreaCode, BurnedMotorCaseStatus, MotorDataOrigin, MotorStatus, RoleName


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PCM_NOTIFICATION_EMAILS=["pcm@maintenance.example.com"],
    DEFAULT_FROM_EMAIL="sgm@maintenance.example.com",
)
class ElectricMotorModuleTests(TestCase):
    def setUp(self):
        self.area_eletrica = Area.objects.create(name="Eletrica", code=AreaCode.ELETRICA)
        self.area_mecanica = Area.objects.create(name="Mecanica", code=AreaCode.MECANICA)
        self.area_instrumentacao = Area.objects.create(name="Instrumentacao", code=AreaCode.INSTRUMENTACAO)
        self.fabrica_araxa = Fabrica.objects.create(name="Araxa", code="ARAXA", is_active=True)
        self.fabrica_perdizes = Fabrica.objects.create(name="Perdizes", code="PERDIZES", is_active=True)
        self.unidade_eletrica = UnidadeProdutiva.objects.create(
            fabrica=self.fabrica_araxa,
            name="Linha 1",
            code="L1",
        )
        self.unidade_mecanica = UnidadeProdutiva.objects.create(
            fabrica=self.fabrica_perdizes,
            name="Linha 4",
            code="L4",
        )
        self.role_manutentor = Role.objects.create(name=RoleName.MANUTENTOR)
        self.role_lider = Role.objects.create(name=RoleName.LIDER)
        self.role_admin = Role.objects.create(name=RoleName.ADMIN)

        self.manutentor = User.objects.create_user(
            email="eletrica.n1@maintenance.example.com",
            password="Teste@123",
            full_name="Manutentor Eletrica N1",
            area=self.area_eletrica,
            role=self.role_manutentor,
            unidade=self.unidade_eletrica,
            is_active=True,
        )
        UserArea.objects.create(user=self.manutentor, area=self.area_eletrica)

        self.lider = User.objects.create_user(
            email="lider.eletrica@maintenance.example.com",
            password="Teste@123",
            full_name="Lider Eletrica",
            area=self.area_eletrica,
            role=self.role_lider,
            unidade=self.unidade_eletrica,
            is_active=True,
        )
        UserArea.objects.create(user=self.lider, area=self.area_eletrica)

        self.mecanico = User.objects.create_user(
            email="mecanica.n1@maintenance.example.com",
            password="Teste@123",
            full_name="Manutentor Mecanica N1",
            area=self.area_mecanica,
            role=self.role_manutentor,
            unidade=self.unidade_mecanica,
            is_active=True,
        )
        UserArea.objects.create(user=self.mecanico, area=self.area_mecanica)

        self.admin = User.objects.create_user(
            email="admin@maintenance.example.com",
            password="Teste@123",
            full_name="Administrador Global",
            area=self.area_mecanica,
            role=self.role_admin,
            is_active=True,
        )
        UserArea.objects.create(user=self.admin, area=self.area_eletrica)
        UserArea.objects.create(user=self.admin, area=self.area_mecanica)
        UserArea.objects.create(user=self.admin, area=self.area_instrumentacao)

        self.motor = ElectricMotor.objects.create(
            area=self.area_eletrica,
            unidade=self.unidade_eletrica,
            mo="MO-100",
            description="Motor principal da linha",
            power="75 CV",
            manufacturer="WEG",
            frame="280S/M",
            rpm=1780,
            voltage="440",
            current="98.5",
            location_name="Oficina eletrica",
            status=MotorStatus.IN_OPERATION,
            registered_by_user=self.lider,
        )
        self.case = BurnedMotorCase.objects.create(
            area=self.area_eletrica,
            motor=self.motor,
            unidade=self.unidade_eletrica,
            process_code="MQ-TESTE-001",
            motor_description="Motor principal da linha",
            motor_mo="MO-100",
            motor_power="75 CV",
            motor_manufacturer="WEG",
            motor_frame="280S/M",
            motor_rpm=1780,
            motor_voltage="440",
            motor_current="98.5",
            motor_location="Oficina eletrica",
            requester_name="Inspetor eletrico",
            problem_type="Bobina em curto",
            defect_description="Motor apresentou aquecimento elevado e travou em operacao.",
            status=BurnedMotorCaseStatus.AWAITING_APPROVAL,
            sent_to_pcm=True,
            sent_to_finance=True,
            opened_by_user=self.lider,
            updated_by_user=self.lider,
        )
        self.client = Client()

    def test_electrical_maintainer_can_view_motor_list(self):
        self.client.force_login(self.manutentor)

        response = self.client.get(reverse("motores:list"), {"area": AreaCode.ELETRICA})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MO-100")
        self.assertContains(response, "75 CV")

    def test_motor_list_filters_by_search_text(self):
        ElectricMotor.objects.create(
            area=self.area_eletrica,
            unidade=self.unidade_eletrica,
            mo="MO-200",
            description="Motor reserva da bomba",
            power="30 CV",
            manufacturer="Siemens",
            frame="225S",
            rpm=1750,
            voltage="380",
            current="54.2",
            status=MotorStatus.RESERVE,
            registered_by_user=self.lider,
        )
        self.client.force_login(self.manutentor)

        response = self.client.get(reverse("motores:list"), {"area": AreaCode.ELETRICA, "search": "Siemens"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MO-200")
        self.assertNotContains(response, "MO-100")

    def test_maintainer_cannot_open_motor_create(self):
        self.client.force_login(self.manutentor)

        response = self.client.get(reverse("motores:create"), {"area": AreaCode.ELETRICA})

        self.assertEqual(response.status_code, 403)

    def test_leader_can_create_motor(self):
        self.client.force_login(self.lider)

        response = self.client.post(
            reverse("motores:create"),
            {
                "mo": "MO-300",
                "description": "Motor reserva da linha 1",
                "unidade": str(self.unidade_eletrica.id),
                "location_name": "Oficina eletrica",
                "power": "50 CV",
                "manufacturer": "ABB",
                "frame": "250M",
                "rpm": 1770,
                "voltage": "440",
                "current": "63.1",
                "status": MotorStatus.RESERVE,
                "notes": "Motor reserva para linha de batata.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(ElectricMotor.objects.filter(mo="MO-300").exists())

    def test_detail_exposes_related_burned_case(self):
        self.client.force_login(self.manutentor)

        response = self.client.get(reverse("motores:detail", kwargs={"pk": self.motor.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.case.process_code)
        self.assertContains(response, "Bobina em curto")

    def test_leader_can_view_burned_case_list(self):
        self.client.force_login(self.lider)

        response = self.client.get(reverse("motores:burned-case-list"), {"area": AreaCode.ELETRICA})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.case.process_code)
        self.assertContains(response, "Motores Queimados")

    def test_maintainer_cannot_open_burned_case_module(self):
        self.client.force_login(self.manutentor)

        response = self.client.get(reverse("motores:burned-case-list"), {"area": AreaCode.ELETRICA})

        self.assertEqual(response.status_code, 403)

    def test_leader_can_create_burned_case_using_registered_motor_and_send_email(self):
        self.client.force_login(self.lider)

        response = self.client.post(
            reverse("motores:burned-case-create"),
            {
                "motor_lookup": str(self.motor.pk),
                "unidade": str(self.unidade_eletrica.id),
                "motor_description": "",
                "motor_mo": "",
                "motor_power": "",
                "motor_manufacturer": "",
                "motor_frame": "",
                "motor_rpm": "",
                "motor_voltage": "",
                "motor_current": "",
                "motor_location": "",
                "occurred_at": "2026-04-07T10:00",
                "requester_name": "Inspetor da oficina",
                "problem_type": "Queima total",
                "defect_description": "Motor encontrado queimado na bancada.",
                "technical_notes": "Cheiro forte de isolacao.",
                "priority": "HIGH",
                "needs_pcm": "on",
                "sent_to_pcm": "",
                "sent_to_pcm_at": "",
                "pcm_responsible": "PCM Central",
                "sent_to_finance": "",
                "finance_sent_at": "",
                "approved": "",
                "approved_at": "",
                "solution_type": "UNDER_EVALUATION",
                "purchase_new_motor": "",
                "rewinding_required": "on",
                "third_party_company": "Rebobinadora XPTO",
                "third_party_contact": "Joao",
                "freight_requested": "",
                "pickup_at": "",
                "expected_return_at": "",
                "arrived_at": "",
                "progress_notes": "Abrindo processo inicial.",
                "status": BurnedMotorCaseStatus.OPEN,
                "_send_pcm": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        created_case = BurnedMotorCase.objects.exclude(pk=self.case.pk).get()
        self.assertEqual(created_case.motor, self.motor)
        self.assertEqual(created_case.motor_mo, "MO-100")
        self.assertTrue(created_case.pcm_email_sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("MO-100", mail.outbox[0].subject)
        self.assertTrue(mail.outbox[0].alternatives)
        self.assertIn("Processo", mail.outbox[0].body)

    def test_leader_can_create_manual_case_and_generate_provisional_motor(self):
        self.client.force_login(self.lider)

        response = self.client.post(
            reverse("motores:burned-case-create"),
            {
                "motor_lookup": "",
                "unidade": str(self.unidade_eletrica.id),
                "motor_description": "Motor do exaustor sul",
                "motor_mo": "",
                "motor_power": "25 CV",
                "motor_manufacturer": "WEG",
                "motor_frame": "200L",
                "motor_rpm": "1750",
                "motor_voltage": "380",
                "motor_current": "44.2",
                "motor_location": "Setor de secagem",
                "create_provisional_motor": "on",
                "occurred_at": "2026-04-07T10:00",
                "requester_name": "Inspetor da oficina",
                "problem_type": "Defeito em enrolamento",
                "defect_description": "Motor queimou antes de seguir para PCM.",
                "technical_notes": "Sem cadastro previo no sistema.",
                "priority": "MEDIUM",
                "needs_pcm": "on",
                "sent_to_pcm": "",
                "sent_to_pcm_at": "",
                "pcm_responsible": "",
                "sent_to_finance": "",
                "finance_sent_at": "",
                "approved": "",
                "approved_at": "",
                "solution_type": "UNDER_EVALUATION",
                "purchase_new_motor": "",
                "rewinding_required": "on",
                "third_party_company": "",
                "third_party_contact": "",
                "freight_requested": "",
                "pickup_at": "",
                "expected_return_at": "",
                "arrived_at": "",
                "progress_notes": "",
                "status": BurnedMotorCaseStatus.IDENTIFIED,
            },
        )

        self.assertEqual(response.status_code, 302)
        created_case = BurnedMotorCase.objects.exclude(pk=self.case.pk).get()
        self.assertIsNotNone(created_case.motor)
        self.assertTrue(created_case.motor.is_provisional)
        self.assertEqual(created_case.data_origin, MotorDataOrigin.PROVISIONAL)

    def test_leader_can_create_manual_case_without_registered_motor(self):
        self.client.force_login(self.lider)

        response = self.client.post(
            reverse("motores:burned-case-create"),
            {
                "motor_lookup": "",
                "unidade": str(self.unidade_eletrica.id),
                "motor_description": "Motor da esteira 4",
                "motor_mo": "SEM-MO-01",
                "motor_power": "15 CV",
                "motor_manufacturer": "WEG",
                "motor_frame": "180L",
                "motor_rpm": "1750",
                "motor_voltage": "380",
                "motor_current": "29.4",
                "motor_location": "Linha de embalagem",
                "occurred_at": "2026-04-07T10:00",
                "requester_name": "Inspetor da oficina",
                "problem_type": "Queima parcial",
                "defect_description": "Motor operou com sobrecorrente e foi retirado.",
                "technical_notes": "Sem cadastro definitivo no momento.",
                "priority": "HIGH",
                "needs_pcm": "on",
                "sent_to_pcm": "",
                "sent_to_pcm_at": "",
                "pcm_responsible": "",
                "sent_to_finance": "",
                "finance_sent_at": "",
                "approved": "",
                "approved_at": "",
                "solution_type": "UNDER_EVALUATION",
                "purchase_new_motor": "",
                "rewinding_required": "",
                "third_party_company": "",
                "third_party_contact": "",
                "freight_requested": "",
                "pickup_at": "",
                "expected_return_at": "",
                "arrived_at": "",
                "progress_notes": "Aguardando triagem inicial.",
                "status": BurnedMotorCaseStatus.IDENTIFIED,
            },
        )

        self.assertEqual(response.status_code, 302)
        created_case = BurnedMotorCase.objects.exclude(pk=self.case.pk).order_by("-created_at").first()
        self.assertIsNotNone(created_case)
        self.assertIsNone(created_case.motor)
        self.assertEqual(created_case.data_origin, MotorDataOrigin.MANUAL)
        self.assertEqual(created_case.motor_mo, "SEM-MO-01")

    def test_status_update_creates_timeline_event(self):
        self.client.force_login(self.lider)

        response = self.client.post(
            reverse("motores:burned-case-status", kwargs={"pk": self.case.pk}),
            {
                "status": BurnedMotorCaseStatus.IN_TRANSPORT,
                "progress_notes": "Coleta confirmada com a transportadora.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.case.refresh_from_db()
        self.assertEqual(self.case.status, BurnedMotorCaseStatus.IN_TRANSPORT)
        self.assertTrue(self.case.events.filter(title__icontains="Status alterado").exists())
        self.assertTrue(self.case.sent_to_pcm)
        self.assertTrue(self.case.sent_to_finance)

    def test_status_update_marks_pcm_milestones(self):
        self.case.sent_to_pcm = False
        self.case.sent_to_pcm_at = None
        self.case.save(update_fields=["sent_to_pcm", "sent_to_pcm_at", "updated_at"])
        self.client.force_login(self.lider)

        response = self.client.post(
            reverse("motores:burned-case-status", kwargs={"pk": self.case.pk}),
            {
                "status": BurnedMotorCaseStatus.SENT_TO_PCM,
                "progress_notes": "PCM acionado pela oficina.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.case.refresh_from_db()
        self.assertEqual(self.case.status, BurnedMotorCaseStatus.SENT_TO_PCM)
        self.assertTrue(self.case.sent_to_pcm)
        self.assertIsNotNone(self.case.sent_to_pcm_at)

    def test_mechanical_user_cannot_access_electrical_motor_module(self):
        self.client.force_login(self.mecanico)

        response = self.client.get(reverse("motores:list"), {"area": AreaCode.MECANICA})

        self.assertEqual(response.status_code, 403)

    def test_admin_with_three_areas_can_access_burned_case_module_without_explicit_area(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("motores:burned-case-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Motores Queimados")
        self.assertContains(response, self.case.process_code)
