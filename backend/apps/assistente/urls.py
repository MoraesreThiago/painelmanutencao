from django.urls import path

from apps.assistente import views


app_name = "assistente"

urlpatterns = [
    path("assistente/chat/", views.AssistantChatView.as_view(), name="chat"),
    path("assistente/chat/enviar/", views.AssistantSubmitView.as_view(), name="submit"),
    path("assistente/chat/nova/", views.AssistantNewChatView.as_view(), name="new"),
]

