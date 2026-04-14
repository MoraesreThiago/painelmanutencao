from django.contrib import admin

from apps.assistente.models import ChatMessage, ChatSession


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    fields = ("role", "content", "created_at")
    readonly_fields = ("created_at",)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "area", "updated_at")
    list_filter = ("area",)
    search_fields = ("title", "user__full_name", "user__email")
    autocomplete_fields = ("user", "area")
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("session__title", "content", "session__user__full_name")
    autocomplete_fields = ("session",)

