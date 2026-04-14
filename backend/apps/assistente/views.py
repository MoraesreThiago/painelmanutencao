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
    get_assistant_allowed_areas,
    get_session_for_user,
    list_recent_sessions,
    resolve_assistant_area,
    submit_prompt,
)
from common.permissions import PermissionName, can_view_area_data, ensure_permission


class AssistantChatView(LoginRequiredMixin, SidebarContextMixin, TemplateView):
    template_name = "assistente/chat.html"
    active_nav_slug = "assistente"

    def dispatch(self, request, *args, **kwargs):
        ensure_permission(request.user, PermissionName.VIEW_AREA_DATA)
        return super().dispatch(request, *args, **kwargs)

    def get_sidebar_area(self):
        explicit_area = resolve_assistant_area(self.request.user, self.request.GET.get("area"))
        if explicit_area is not None:
            return explicit_area
        session = self.get_session()
        if session is not None and session.area_id:
            return session.area
        return None

    def get_session(self):
        return get_session_for_user(self.request.user, self.request.GET.get("session"))

    def get_form(self):
        initial = {}
        session = self.get_session()
        area = self.get_sidebar_area()
        if session is not None:
            initial["session_id"] = session.id
            if session.area_id:
                initial["area"] = str(session.area.code)
        elif area is not None:
            initial["area"] = str(area.code)
        return ChatPromptForm(allowed_areas=get_assistant_allowed_areas(self.request.user), initial=initial)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.get_session()
        context.update(
            {
                "page_title": "Assistente IA",
                "page_eyebrow": "Analise operacional",
                "chat_form": self.get_form(),
                "chat_session": session,
                "chat_messages": list(session.messages.all()) if session else [],
                "recent_sessions": list_recent_sessions(self.request.user),
                "suggested_prompts": [
                    "Me fale os principais motivos das ocorrencias dos ultimos 3 meses.",
                    "Mostre as ocorrencias em aberto e os equipamentos mais afetados.",
                    "Resuma o tempo de parada registrado nos ultimos 90 dias.",
                ],
            }
        )
        return context


class AssistantSubmitView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        ensure_permission(request.user, PermissionName.VIEW_AREA_DATA)
        form = ChatPromptForm(request.POST, allowed_areas=get_assistant_allowed_areas(request.user))
        session = get_session_for_user(request.user, request.POST.get("session_id"))
        area = resolve_assistant_area(request.user, request.POST.get("area"))

        if form.is_valid():
            session = submit_prompt(
                user=request.user,
                prompt=form.cleaned_data["prompt"],
                area=area,
                session=session,
            )
            form = ChatPromptForm(
                allowed_areas=get_assistant_allowed_areas(request.user),
                initial={
                    "session_id": session.id,
                    "area": str(session.area.code) if session.area_id else "",
                },
            )
        else:
            form.fields["session_id"].initial = request.POST.get("session_id")
            form.fields["area"].initial = request.POST.get("area")

        context = {
            "chat_form": form,
            "chat_session": session,
            "chat_messages": list(session.messages.all()) if session else [],
        }
        response = TemplateResponse(request, "assistente/partials/workspace.html", context)
        if session is not None:
            query_items = [f"session={session.id}"]
            if session.area_id:
                query_items.append(f"area={session.area.code}")
            response["HX-Push-Url"] = f"{reverse('assistente:chat')}?{'&'.join(query_items)}"
        return response


class AssistantNewChatView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        ensure_permission(request.user, PermissionName.VIEW_AREA_DATA)
        area_code = request.GET.get("area")
        target = reverse("assistente:chat")
        if area_code:
            target = f"{target}?area={area_code}"
        return redirect(target)
