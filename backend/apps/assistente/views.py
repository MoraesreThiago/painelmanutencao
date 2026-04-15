from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.access.mixins import SidebarContextMixin
from apps.assistente.forms import ChatPromptForm
from apps.assistente.services import (
    get_session_for_user,
    list_recent_sessions,
    resolve_assistant_area,
    submit_prompt,
)
from common.permissions import PermissionName, ensure_permission


SUGGESTED_PROMPTS = [
    "Me fale os principais motivos das ocorrencias dos ultimos 3 meses.",
    "Mostre as ocorrencias em aberto e os equipamentos mais afetados.",
    "Resuma o tempo de parada registrado nos ultimos 90 dias.",
]


def build_chat_url(*, area=None, session=None) -> str:
    query_items = []
    if session is not None:
        query_items.append(f"session={session.id}")
    if area is not None:
        query_items.append(f"area={area.code}")
    base_url = reverse("assistente:chat")
    if not query_items:
        return base_url
    return f"{base_url}?{'&'.join(query_items)}"


def build_assistant_context(*, user, area, session, form, history_oob=False):
    return {
        "chat_form": form,
        "chat_session": session,
        "chat_messages": list(session.messages.all()) if session else [],
        "current_area": area,
        "recent_sessions": list_recent_sessions(user, area=area),
        "suggested_prompts": SUGGESTED_PROMPTS,
        "assistant_scope_label": area.name if area is not None else "Todas as areas permitidas",
        "chat_submit_url": reverse("assistente:submit")
        if area is None
        else f"{reverse('assistente:submit')}?area={area.code}",
        "chat_new_url": reverse("assistente:new")
        if area is None
        else f"{reverse('assistente:new')}?area={area.code}",
        "history_oob": history_oob,
    }


class AssistantChatView(LoginRequiredMixin, SidebarContextMixin, TemplateView):
    template_name = "assistente/chat.html"
    active_nav_slug = "assistente"

    def dispatch(self, request, *args, **kwargs):
        ensure_permission(request.user, PermissionName.VIEW_AREA_DATA)
        return super().dispatch(request, *args, **kwargs)

    def get_sidebar_area(self):
        return resolve_assistant_area(self.request.user, self.request.GET.get("area"))

    def get_session(self):
        return get_session_for_user(
            self.request.user,
            self.request.GET.get("session"),
            area=self.get_sidebar_area(),
        )

    def get_form(self):
        initial = {}
        session = self.get_session()
        if session is not None:
            initial["session_id"] = session.id
        return ChatPromptForm(initial=initial)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        area = self.get_sidebar_area()
        context["page_title"] = "Assistente IA"
        context["page_eyebrow"] = area.name if area is not None else "Analise operacional"
        context.update(
            build_assistant_context(
                user=self.request.user,
                area=area,
                session=self.get_session(),
                form=self.get_form(),
            )
        )
        return context


class AssistantSubmitView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        ensure_permission(request.user, PermissionName.VIEW_AREA_DATA)
        area = resolve_assistant_area(request.user, request.GET.get("area"))
        form = ChatPromptForm(request.POST)
        session = get_session_for_user(request.user, request.POST.get("session_id"), area=area)

        if form.is_valid():
            session = submit_prompt(
                user=request.user,
                prompt=form.cleaned_data["prompt"],
                area=area,
                session=session,
            )
            form = ChatPromptForm(initial={"session_id": session.id})
        else:
            form.fields["session_id"].initial = request.POST.get("session_id")

        context = build_assistant_context(
            user=request.user,
            area=area,
            session=session,
            form=form,
            history_oob=True,
        )
        response = TemplateResponse(request, "assistente/partials/workspace.html", context)
        if session is not None:
            response["HX-Push-Url"] = build_chat_url(area=area or session.area, session=session)
        return response


class AssistantNewChatView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        ensure_permission(request.user, PermissionName.VIEW_AREA_DATA)
        area = resolve_assistant_area(request.user, request.GET.get("area"))
        return redirect(build_chat_url(area=area))
