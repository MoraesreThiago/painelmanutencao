from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.access.models import Role, UserArea
from apps.accounts.models import User
from apps.equipamentos.models import Equipment, Motor
from apps.ordens_servico.models import ExternalServiceOrder
from apps.unidades.models import Area, Location
from common.enums import AreaCode, EquipmentStatus, EquipmentType, ExternalServiceStatus, RoleName


class ServiceOrderModuleTests(TestCase):
    def setUp(self):
        self.area_eletrica = Area.objects.create(name="Eletrica", code=AreaCode.ELETRICA)
        self.area_mecanica = Area.objects.create(name="Mecanica", code=AreaCode.MECANICA)
        self.location_eletrica = Location.objects.create(name="Sala eletrica", sector="Utilidades", area=self.area_eletrica)
        self.location_mecanica = Location.objects.create(name="Oficina", sector="Planta", area=self.area_mecanica)

        self.role_manutentor = Role.objects.create(name=RoleName.MANUTENTOR)
        self.user = User.objects.create_user(
            email="os.eletrica@maintenance.example.com",
            password="Teste@123",
            full_name="Manutentor Eletrica OS",
            area=self.area_eletrica,
            role=self.role_manutentor,
            is_active=True,
        )
        UserArea.objects.create(user=self.user, area=self.area_eletrica)

        self.equipment_eletrica = Equipment.objects.create(
            code="MTR-100",
            tag="TAG-MTR-100",
            description="Motor do exaustor",
            sector="Utilidades",
            type=EquipmentType.MOTOR,
            status=EquipmentStatus.EXTERNAL_SERVICE,
            registered_at=timezone.now(),
            area=self.area_eletrica,
            location=self.location_eletrica,
        )
        self.motor_eletrica = Motor.objects.create(
            equipment=self.equipment_eletrica,
            unique_identifier="ME-100",
        )

        self.equipment_mecanica = Equipment.objects.create(
            code="MTR-200",
            tag="TAG-MTR-200",
            description="Motor de bomba",
            sector="Planta",
            type=EquipmentType.MOTOR,
            status=EquipmentStatus.EXTERNAL_SERVICE,
            registered_at=timezone.now(),
            area=self.area_mecanica,
            location=self.location_mecanica,
        )
        self.motor_mecanica = Motor.objects.create(
            equipment=self.equipment_mecanica,
            unique_identifier="MM-200",
        )

        self.order_eletrica = ExternalServiceOrder.objects.create(
            motor=self.motor_eletrica,
            reason="Bobinagem",
            vendor_name="Fornecedor A",
            work_order_number="OS-100",
            authorized_by_user=self.user,
            registered_by_user=self.user,
            service_status=ExternalServiceStatus.OPEN,
        )
        self.order_mecanica = ExternalServiceOrder.objects.create(
            motor=self.motor_mecanica,
            reason="Avaliacao",
            vendor_name="Fornecedor B",
            work_order_number="OS-200",
            authorized_by_user=self.user,
            registered_by_user=self.user,
            service_status=ExternalServiceStatus.OPEN,
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_service_order_list_is_scoped_to_user_area(self):
        response = self.client.get(reverse("ordens-servico:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "OS-100")
        self.assertNotContains(response, "OS-200")
        self.assertContains(response, "Ordens de Serviço")

    def test_service_order_detail_requires_area_access(self):
        response = self.client.get(reverse("ordens-servico:detail", kwargs={"pk": self.order_mecanica.pk}))
        self.assertEqual(response.status_code, 403)
