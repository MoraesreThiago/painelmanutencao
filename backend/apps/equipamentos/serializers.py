from django.utils import timezone
from rest_framework import serializers

from apps.equipamentos.models import Equipment
from apps.unidades.models import Area, Location, UnidadeProdutiva


class EquipmentSummarySerializer(serializers.ModelSerializer):
    area_name = serializers.CharField(source="area.name", read_only=True)
    area_code = serializers.CharField(source="area.code", read_only=True)
    fabrica_code = serializers.CharField(source="resolved_fabrica.code", read_only=True, default=None)
    fabrica_name = serializers.CharField(source="resolved_fabrica.name", read_only=True, default=None)
    unidade_id = serializers.CharField(source="resolved_unidade.id", read_only=True, default=None)
    unidade_name = serializers.CharField(source="resolved_unidade.name", read_only=True, default=None)
    location_name = serializers.CharField(source="location.name", read_only=True, default=None)

    class Meta:
        model = Equipment
        fields = [
            "id",
            "code",
            "tag",
            "description",
            "sector",
            "type",
            "status",
            "area_code",
            "area_name",
            "fabrica_code",
            "fabrica_name",
            "unidade_id",
            "unidade_name",
            "location_name",
        ]


class EquipmentDetailSerializer(EquipmentSummarySerializer):
    motor_identifier = serializers.CharField(source="motor.unique_identifier", read_only=True, default=None)
    instrument_identifier = serializers.CharField(source="instrument.unique_identifier", read_only=True, default=None)

    class Meta(EquipmentSummarySerializer.Meta):
        fields = EquipmentSummarySerializer.Meta.fields + [
            "manufacturer",
            "model",
            "serial_number",
            "notes",
            "registered_at",
            "motor_identifier",
            "instrument_identifier",
        ]


class EquipmentWriteSerializer(serializers.ModelSerializer):
    area = serializers.PrimaryKeyRelatedField(queryset=Area.objects.all())
    unidade = serializers.PrimaryKeyRelatedField(queryset=UnidadeProdutiva.objects.all(), allow_null=True, required=False)
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all(), allow_null=True, required=False)
    registered_at = serializers.DateTimeField(required=False, default=timezone.now)

    class Meta:
        model = Equipment
        fields = [
            "id",
            "code",
            "tag",
            "description",
            "sector",
            "manufacturer",
            "model",
            "serial_number",
            "notes",
            "type",
            "status",
            "registered_at",
            "area",
            "unidade",
            "location",
        ]

    def validate(self, attrs):
        area = attrs.get("area", getattr(self.instance, "area", None))
        unidade = attrs.get("unidade", getattr(self.instance, "unidade", None))
        location = attrs.get("location", getattr(self.instance, "location", None))
        if not attrs.get("registered_at") and self.instance is None:
            attrs["registered_at"] = timezone.now()
        if location and area and location.area_id != area.id:
            raise serializers.ValidationError({"location": "A unidade/local precisa pertencer a mesma area do equipamento."})
        if location and location.unidade_id:
            if unidade and location.unidade_id != unidade.id:
                raise serializers.ValidationError({"location": "O local selecionado nao pertence a unidade produtiva informada."})
            if not unidade:
                attrs["unidade"] = location.unidade
                unidade = location.unidade
        if unidade is None:
            raise serializers.ValidationError({"unidade": "Selecione a unidade produtiva do equipamento."})
        return attrs
