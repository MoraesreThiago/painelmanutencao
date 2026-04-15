from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.access.models import Role, UserArea
from apps.assistente.models import ChatMessage, ChatSession
from apps.accounts.models import User
from apps.unidades.models import Area
from common.enums import AreaCode, RoleName


class AssistantChatTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(name="Eletrica", code=AreaCode.ELETRICA)
        self.other_area = Area.objects.create(name="Mecanica", code=AreaCode.MECANICA)
        self.role = Role.objects.create(name=RoleName.MANUTENTOR)
        self.user = User.objects.create_user(
            email="assistente.eletrica@maintenance.example.com",
            password="Teste@123",
            full_name="Assistente Eletrica",
            area=self.area,
            role=self.role,
            is_active=True,
        )
        UserArea.objects.create(user=self.user, area=self.area)
        self.client = Client()
        self.client.force_login(self.user)

    def test_chat_page_is_available(self):
        response = self.client.get(reverse("assistente:chat"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Assistente IA")
        self.assertContains(response, "Chat IA")
        self.assertContains(response, "Area atual: Eletrica.")
        self.assertNotContains(response, 'name="area"', html=False)

    @override_settings(OPENAI_API_KEY=None)
    def test_chat_submit_creates_session_and_fallback_reply(self):
        response = self.client.post(
            reverse("assistente:submit"),
            {
                "prompt": "Mostre as ocorrencias dos ultimos 3 meses.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatSession.objects.count(), 1)
        self.assertEqual(ChatMessage.objects.count(), 2)
        self.assertEqual(ChatSession.objects.first().area, self.area)
        assistant_message = ChatMessage.objects.filter(role=ChatMessage.Role.ASSISTANT).first()
        self.assertIsNotNone(assistant_message)
        self.assertIn("OPENAI_API_KEY", assistant_message.content)
        self.assertIn("HX-Push-Url", response.headers)
        self.assertIn("area=ELETRICA", response.headers["HX-Push-Url"])

    def test_chat_area_scope_requires_access(self):
        response = self.client.get(reverse("assistente:chat"), {"area": str(self.other_area.code)})
        self.assertEqual(response.status_code, 403)
