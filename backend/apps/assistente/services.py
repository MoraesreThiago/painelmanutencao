from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.text import Truncator

from apps.assistente.models import ChatMessage, ChatSession
from apps.ocorrencias.models import Occurrence
from apps.unidades.models import Area
from common.enums import OccurrenceClassification, OccurrenceStatus
from common.permissions import ensure_area_access, get_allowed_areas, is_global_user


def get_assistant_allowed_areas(user):
    if is_global_user(user):
        return list(Area.objects.order_by("name"))
    return get_allowed_areas(user)


def resolve_assistant_area(user, area_code: str | None):
    if not area_code:
        return None
    area = Area.objects.filter(code=area_code).first()
    if area is None:
        return None
    ensure_area_access(user, area)
    return area


def list_recent_sessions(user, *, limit: int = 6):
    return ChatSession.objects.filter(user=user).select_related("area")[:limit]


def get_session_for_user(user, session_id):
    if not session_id:
        return None
    return ChatSession.objects.filter(user=user, pk=session_id).select_related("area").first()


def _build_openai_client():
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None
    return OpenAI(api_key=api_key)


def _base_occurrence_queryset(user, area=None):
    queryset = Occurrence.objects.select_related("equipment", "area", "location").order_by("-occurred_at")
    if area is not None:
        return queryset.filter(area=area)
    allowed_areas = get_assistant_allowed_areas(user)
    if allowed_areas:
        return queryset.filter(area__in=allowed_areas)
    return queryset.none()


def _build_occurrence_context(user, area=None) -> str:
    now = timezone.now()
    since = now - timedelta(days=90)
    queryset = _base_occurrence_queryset(user, area=area).filter(occurred_at__gte=since)

    total_occurrences = queryset.count()
    total_downtime = queryset.aggregate(total=Sum("downtime_minutes"))["total"] or 0

    status_summary = [
        f"- {OccurrenceStatus(item['status']).label}: {item['total']}"
        for item in queryset.values("status").annotate(total=Count("id")).order_by("-total", "status")
    ]
    classification_summary = [
        f"- {OccurrenceClassification(item['classification']).label}: {item['total']}"
        for item in queryset.values("classification")
        .annotate(total=Count("id"))
        .order_by("-total", "classification")
    ]
    recent_occurrences = [
        (
            f"- {occurrence.occurred_at:%d/%m/%Y %H:%M} | "
            f"{occurrence.area.name} | "
            f"{occurrence.equipment.code} | "
            f"{occurrence.get_status_display()} | "
            f"{Truncator(occurrence.description).chars(140)}"
        )
        for occurrence in queryset[:20]
    ]

    area_label = area.name if area is not None else "todas as areas permitidas"
    context_lines = [
        f"Janela analisada: ultimos 90 dias ate {now:%d/%m/%Y %H:%M}.",
        f"Escopo de area: {area_label}.",
        f"Total de ocorrencias no periodo: {total_occurrences}.",
        f"Tempo total de parada registrado: {total_downtime} minutos.",
        "Resumo por status:",
        *(status_summary or ["- Sem dados"]),
        "Resumo por classificacao:",
        *(classification_summary or ["- Sem dados"]),
        "Ocorrencias recentes:",
        *(recent_occurrences or ["- Sem ocorrencias recentes no periodo"]),
    ]
    return "\n".join(context_lines)


def _build_model_input(session: ChatSession, context_block: str):
    history_items = [
        {
            "role": "system",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "Voce e um assistente operacional industrial. "
                        "Responda em portugues do Brasil, de forma objetiva e clara. "
                        "Use apenas o contexto operacional fornecido. "
                        "Se o contexto nao for suficiente, diga isso claramente. "
                        "Nao invente ocorrencias, causas, metricas ou equipamentos."
                    ),
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "Contexto operacional para responder perguntas sobre ocorrencias e operacao:\n"
                        f"{context_block}"
                    ),
                }
            ],
        },
    ]
    for message in session.messages.order_by("created_at"):
        history_items.append(
            {
                "role": "user" if message.role == ChatMessage.Role.USER else "assistant",
                "content": [
                    {
                        "type": "input_text",
                        "text": message.content,
                    }
                ],
            }
        )
    return history_items


def _generate_assistant_reply(session: ChatSession, *, area=None) -> str:
    client = _build_openai_client()
    if client is None:
        return (
            "O chat esta pronto, mas a integracao com a OpenAI ainda nao foi configurada. "
            "Defina OPENAI_API_KEY no ambiente para receber respostas geradas pela IA."
        )

    context_block = _build_occurrence_context(session.user, area=area)
    model = getattr(settings, "OPENAI_CHAT_MODEL", "gpt-5")
    try:
        response = client.responses.create(
            model=model,
            store=False,
            input=_build_model_input(session, context_block),
        )
        output_text = (response.output_text or "").strip()
        if output_text:
            return output_text
    except Exception:
        return (
            "Nao consegui consultar a IA agora. "
            "Tente novamente em instantes ou revise a configuracao da integracao OpenAI."
        )
    return "Nao consegui gerar uma resposta valida com os dados disponiveis."


@transaction.atomic
def submit_prompt(*, user, prompt: str, area=None, session: ChatSession | None = None) -> ChatSession:
    if session is None:
        session = ChatSession.objects.create(
            user=user,
            area=area,
            title=Truncator(prompt).chars(80),
        )
    elif not session.title:
        session.title = Truncator(prompt).chars(80)
        session.save(update_fields=["title", "updated_at"])

    if area is not None and session.area_id != area.id:
        session.area = area
        session.save(update_fields=["area", "updated_at"])

    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content=prompt,
    )
    assistant_reply = _generate_assistant_reply(session, area=area or session.area)
    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content=assistant_reply,
    )
    session.save(update_fields=["updated_at"])
    return session
