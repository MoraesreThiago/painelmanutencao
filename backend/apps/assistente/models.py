from __future__ import annotations

from django.db import models

from common.models import UUIDTimeStampedModel


class ChatSession(UUIDTimeStampedModel):
    user = models.ForeignKey("accounts.User", related_name="chat_sessions", on_delete=models.CASCADE)
    area = models.ForeignKey(
        "unidades.Area",
        related_name="chat_sessions",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]
        verbose_name = "Sessao de chat"
        verbose_name_plural = "Sessoes de chat"

    def __str__(self) -> str:
        return self.title or f"Chat {self.created_at:%d/%m/%Y %H:%M}"


class ChatMessage(UUIDTimeStampedModel):
    class Role(models.TextChoices):
        USER = "USER", "Usuario"
        ASSISTANT = "ASSISTANT", "Assistente"

    session = models.ForeignKey("assistente.ChatSession", related_name="messages", on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name = "Mensagem de chat"
        verbose_name_plural = "Mensagens de chat"

    def __str__(self) -> str:
        return f"{self.get_role_display()} - {self.created_at:%d/%m/%Y %H:%M}"

