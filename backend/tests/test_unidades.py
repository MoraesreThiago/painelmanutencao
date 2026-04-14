from django.test import TestCase

from apps.access.models import Role
from apps.accounts.models import User
from apps.unidades.models import Area, Fabrica, UnidadeProdutiva
from apps.unidades.services import get_fabricas_visiveis, get_unidades_visiveis, pode_acessar_unidade
from common.enums import AreaCode, RoleName


class UnidadeEscopoServicesTests(TestCase):
    def setUp(self):
        self.area_eletrica = Area.objects.create(name="Eletrica", code=AreaCode.ELETRICA)
        self.area_mecanica = Area.objects.create(name="Mecanica", code=AreaCode.MECANICA)
        self.area_instrumentacao = Area.objects.create(name="Instrumentacao", code=AreaCode.INSTRUMENTACAO)

        self.role_gerente = Role.objects.create(name=RoleName.GERENTE)
        self.role_supervisor = Role.objects.create(name=RoleName.SUPERVISOR)
        self.role_lider = Role.objects.create(name=RoleName.LIDER)
        self.role_inspetor = Role.objects.create(name=RoleName.INSPETOR)
        self.role_manutentor = Role.objects.create(name=RoleName.MANUTENTOR)

        self.fabrica_araxa = Fabrica.objects.create(name="Araxa", code="ARAXA", is_active=True)
        self.fabrica_perdizes = Fabrica.objects.create(name="Perdizes", code="PERDIZES", is_active=True)

        self.unidade_linha_1 = UnidadeProdutiva.objects.create(fabrica=self.fabrica_araxa, name="Linha 1", code="L1")
        self.unidade_linha_2 = UnidadeProdutiva.objects.create(fabrica=self.fabrica_araxa, name="Linha 2", code="L2")
        self.unidade_flocos = UnidadeProdutiva.objects.create(fabrica=self.fabrica_araxa, name="Flocos", code="FLOCOS")
        self.unidade_linha_3 = UnidadeProdutiva.objects.create(fabrica=self.fabrica_perdizes, name="Linha 3", code="L3")
        self.unidade_linha_4 = UnidadeProdutiva.objects.create(fabrica=self.fabrica_perdizes, name="Linha 4", code="L4")

        self.gerente = User.objects.create_user(
            email="gerente@maintenance.example.com",
            password="Teste@123",
            full_name="Gerente Manutencao",
            area=self.area_eletrica,
            role=self.role_gerente,
            is_active=True,
        )
        self.supervisor_eletrica = User.objects.create_user(
            email="sup.eletrica@maintenance.example.com",
            password="Teste@123",
            full_name="Supervisor Eletrica",
            area=self.area_eletrica,
            role=self.role_supervisor,
            is_active=True,
        )
        self.supervisor_instrumentacao = User.objects.create_user(
            email="sup.instrumentacao@maintenance.example.com",
            password="Teste@123",
            full_name="Supervisor Instrumentacao",
            area=self.area_instrumentacao,
            role=self.role_supervisor,
            is_active=True,
        )
        self.supervisor_mecanica = User.objects.create_user(
            email="sup.mecanica@maintenance.example.com",
            password="Teste@123",
            full_name="Supervisor Mecanica",
            area=self.area_mecanica,
            role=self.role_supervisor,
            fabrica=self.fabrica_araxa,
            is_active=True,
        )
        self.lider = User.objects.create_user(
            email="lider@maintenance.example.com",
            password="Teste@123",
            full_name="Lider Linha 1",
            area=self.area_eletrica,
            role=self.role_lider,
            unidade=self.unidade_linha_1,
            is_active=True,
        )
        self.inspetor = User.objects.create_user(
            email="inspetor@maintenance.example.com",
            password="Teste@123",
            full_name="Inspetor Linha 3",
            area=self.area_instrumentacao,
            role=self.role_inspetor,
            unidade=self.unidade_linha_3,
            is_active=True,
        )
        self.manutentor = User.objects.create_user(
            email="manutentor@maintenance.example.com",
            password="Teste@123",
            full_name="Manutentor Flocos",
            area=self.area_mecanica,
            role=self.role_manutentor,
            unidade=self.unidade_flocos,
            is_active=True,
        )

    def test_get_unidades_visiveis_para_cada_perfil(self):
        self.assertCountEqual(
            get_unidades_visiveis(self.gerente).values_list("code", flat=True),
            ["L1", "L2", "FLOCOS", "L3", "L4"],
        )
        self.assertCountEqual(
            get_unidades_visiveis(self.supervisor_eletrica).values_list("code", flat=True),
            ["L1", "L2", "FLOCOS", "L3", "L4"],
        )
        self.assertCountEqual(
            get_unidades_visiveis(self.supervisor_instrumentacao).values_list("code", flat=True),
            ["L1", "L2", "FLOCOS", "L3", "L4"],
        )
        self.assertCountEqual(
            get_unidades_visiveis(self.supervisor_mecanica).values_list("code", flat=True),
            ["L1", "L2", "FLOCOS"],
        )
        self.assertCountEqual(
            get_unidades_visiveis(self.lider).values_list("code", flat=True),
            ["L1"],
        )
        self.assertCountEqual(
            get_unidades_visiveis(self.inspetor).values_list("code", flat=True),
            ["L3"],
        )
        self.assertCountEqual(
            get_unidades_visiveis(self.manutentor).values_list("code", flat=True),
            ["FLOCOS"],
        )

    def test_get_fabricas_visiveis_respeita_regras_de_escopo(self):
        self.assertCountEqual(
            get_fabricas_visiveis(self.gerente).values_list("code", flat=True),
            ["ARAXA", "PERDIZES"],
        )
        self.assertCountEqual(
            get_fabricas_visiveis(self.supervisor_eletrica).values_list("code", flat=True),
            ["ARAXA", "PERDIZES"],
        )
        self.assertCountEqual(
            get_fabricas_visiveis(self.supervisor_instrumentacao).values_list("code", flat=True),
            ["ARAXA", "PERDIZES"],
        )
        self.assertCountEqual(
            get_fabricas_visiveis(self.supervisor_mecanica).values_list("code", flat=True),
            ["ARAXA"],
        )
        self.assertCountEqual(
            get_fabricas_visiveis(self.lider).values_list("code", flat=True),
            ["ARAXA"],
        )
        self.assertCountEqual(
            get_fabricas_visiveis(self.inspetor).values_list("code", flat=True),
            ["PERDIZES"],
        )
        self.assertCountEqual(
            get_fabricas_visiveis(self.manutentor).values_list("code", flat=True),
            ["ARAXA"],
        )

    def test_pode_acessar_unidade_para_acesso_valido_e_negado(self):
        self.assertTrue(pode_acessar_unidade(self.supervisor_mecanica, self.unidade_linha_2.id))
        self.assertFalse(pode_acessar_unidade(self.supervisor_mecanica, self.unidade_linha_4.id))
        self.assertTrue(pode_acessar_unidade(self.lider, self.unidade_linha_1.id))
        self.assertFalse(pode_acessar_unidade(self.lider, self.unidade_linha_2.id))
        self.assertTrue(pode_acessar_unidade(self.inspetor, self.unidade_linha_3.id))
        self.assertFalse(pode_acessar_unidade(self.inspetor, self.unidade_linha_1.id))
