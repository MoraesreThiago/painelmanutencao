from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.colaboradores.models import Collaborator
from apps.ocorrencias.models import Occurrence
from apps.ocorrencias.services import build_occurrence_timeline
from apps.unidades.models import Area, Location


class OccurrenceTimelineEventSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    action = serializers.CharField()
    summary = serializers.CharField(allow_blank=True, allow_null=True)
    actor_name = serializers.CharField(allow_blank=True, allow_null=True)
    created_at = serializers.DateTimeField()


class OccurrenceSummarySerializer(serializers.ModelSerializer):
    equipment_code = serializers.CharField(source="equipment.code", read_only=True)
    equipment_description = serializers.CharField(source="equipment.description", read_only=True)
    area_code = serializers.CharField(source="area.code", read_only=True)
    area_name = serializers.CharField(source="area.name", read_only=True)
    fabrica_code = serializers.CharField(source="resolved_fabrica.code", read_only=True, default=None)
    fabrica_name = serializers.CharField(source="resolved_fabrica.name", read_only=True, default=None)
    unidade_id = serializers.CharField(source="resolved_unidade.id", read_only=True, default=None)
    unidade_name = serializers.CharField(source="resolved_unidade.name", read_only=True, default=None)
    location_name = serializers.CharField(source="location.name", read_only=True, default=None)
    responsible_name = serializers.CharField(source="responsible_collaborator.full_name", read_only=True, default=None)

    class Meta:
        model = Occurrence
        fields = [
            "id",
            "equipment",
            "equipment_code",
            "equipment_description",
            "area_code",
            "area_name",
            "fabrica_code",
            "fabrica_name",
            "unidade_id",
            "unidade_name",
            "location_name",
            "classification",
            "status",
            "occurred_at",
            "had_downtime",
            "downtime_minutes",
            "responsible_name",
            "description",
        ]


class OccurrenceDetailSerializer(OccurrenceSummarySerializer):
    reported_by_name = serializers.CharField(source="reported_by_user.full_name", read_only=True, default=None)
    notes = serializers.CharField(allow_blank=True, allow_null=True)
    resolved_at = serializers.DateTimeField(allow_null=True)
    timeline = serializers.SerializerMethodField()

    class Meta(OccurrenceSummarySerializer.Meta):
        fields = OccurrenceSummarySerializer.Meta.fields + [
            "reported_by_name",
            "notes",
            "resolved_at",
            "timeline",
        ]

    def get_timeline(self, obj):
        events = build_occurrence_timeline(obj)[:12]
        return [
            {
                "id": str(event.id),
                "action": event.action,
                "summary": event.summary,
                "actor_name": getattr(event.actor_user, "full_name", None),
                "created_at": event.created_at,
            }
            for event in events
        ]


class OccurrenceWriteSerializer(serializers.ModelSerializer):
    area = serializers.PrimaryKeyRelatedField(queryset=Area.objects.all(), required=False)
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all(), allow_null=True, required=False)
    responsible_collaborator = serializers.PrimaryKeyRelatedField(
        queryset=Collaborator.objects.all(),
        allow_null=True,
        required=False,
    )
    occurred_at = serializers.DateTimeField(required=False, default=timezone.now)
    downtime_minutes = serializers.IntegerField(required=False, allow_null=True, min_value=0)

    class Meta:
        model = Occurrence
        fields = [
            "id",
            "equipment",
            "area",
            "location",
            "classification",
            "status",
            "responsible_collaborator",
            "occurred_at",
            "resolved_at",
            "description",
            "notes",
            "had_downtime",
            "downtime_minutes",
        ]
        extra_kwargs = {
            "resolved_at": {"required": False, "allow_null": True},
            "status": {"required": False},
            "had_downtime": {"required": False},
        }

    def validate(self, attrs):
        equipment = attrs.get("equipment", getattr(self.instance, "equipment", None))
        area = attrs.get("area", getattr(self.instance, "area", None))
        location = attrs.get("location", getattr(self.instance, "location", None))
        collaborator = attrs.get("responsible_collaborator", getattr(self.instance, "responsible_collaborator", None))
        had_downtime = attrs.get("had_downtime", getattr(self.instance, "had_downtime", False))

        if equipment and area and equipment.area_id != area.id:
            raise serializers.ValidationError({"area": "A area precisa corresponder a area do equipamento informado."})
        if equipment and not area:
            attrs["area"] = equipment.area
        if location and equipment and location.area_id != equipment.area_id:
            raise serializers.ValidationError({"location": "A unidade/local precisa pertencer a mesma area do equipamento."})
        if location and equipment and location.unidade_id and equipment.resolved_unidade and location.unidade_id != equipment.resolved_unidade.id:
            raise serializers.ValidationError({"location": "O local selecionado precisa pertencer a mesma unidade produtiva do equipamento."})
        if collaborator and equipment and collaborator.area_id != equipment.area_id:
            raise serializers.ValidationError(
                {"responsible_collaborator": "O responsavel precisa pertencer a mesma area do equipamento."}
            )
        if attrs.get("occurred_at") is None and self.instance is None:
            attrs["occurred_at"] = timezone.now()
        if had_downtime is False:
            attrs["downtime_minutes"] = None
        return attrs


class OccurrenceStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Occurrence._meta.get_field("status").choices)
    note = serializers.CharField(required=False, allow_blank=True)
