from rest_framework import serializers

from apps.accounts.models import User
from common.permissions import get_allowed_areas


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    remember_me = serializers.BooleanField(default=False, required=False)


class UserSummarySerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role.name", default=None)
    primary_area = serializers.CharField(source="area.code", default=None)
    fabrica = serializers.CharField(source="fabrica.code", default=None)
    unidade = serializers.CharField(source="unidade.code", default=None)
    areas = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "registration_number",
            "job_title",
            "role",
            "primary_area",
            "fabrica",
            "unidade",
            "areas",
            "permissions",
        ]

    def get_areas(self, obj):
        return [area.code for area in get_allowed_areas(obj)]

    def get_permissions(self, obj):
        return sorted(obj.permissions)


class OutboxItemSerializer(serializers.Serializer):
    entity_name = serializers.CharField()
    entity_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    action = serializers.CharField()
    payload = serializers.JSONField()


class OutboxBatchSerializer(serializers.Serializer):
    items = OutboxItemSerializer(many=True)
