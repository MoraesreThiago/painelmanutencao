from __future__ import annotations

from django.contrib.auth import login, logout
from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from api.v1.serializers import LoginSerializer, OutboxBatchSerializer, UserSummarySerializer
from apps.accounts.services import authenticate_user
from apps.access.services import build_dashboard_payload
from apps.equipamentos.models import Equipment
from apps.equipamentos.serializers import EquipmentDetailSerializer, EquipmentSummarySerializer, EquipmentWriteSerializer
from apps.equipamentos.services import apply_equipment_filters, base_equipment_queryset, toggle_equipment_active_state
from apps.integracoes.services import enqueue_sync_item
from apps.ocorrencias.models import Occurrence
from apps.ocorrencias.serializers import (
    OccurrenceDetailSerializer,
    OccurrenceStatusUpdateSerializer,
    OccurrenceSummarySerializer,
    OccurrenceWriteSerializer,
)
from apps.ocorrencias.services import (
    apply_occurrence_filters,
    base_occurrence_queryset,
    create_occurrence_from_api,
    update_occurrence_from_api,
    update_occurrence_status,
)
from apps.unidades.models import Area
from common.permissions import PermissionName, ensure_area_access, ensure_permission, get_allowed_areas


class SessionLoginApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate_user(
            request=request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if not user or not user.is_active:
            return Response({"detail": "Credenciais invalidas."}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)
        request.session.set_expiry(None if serializer.validated_data.get("remember_me") else 0)
        return Response(UserSummarySerializer(user).data)


class SessionLogoutApiView(APIView):
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserApiView(APIView):
    def get(self, request, *args, **kwargs):
        return Response(UserSummarySerializer(request.user).data)


class DashboardApiView(APIView):
    def get(self, request, *args, **kwargs):
        area_code = request.query_params.get("area")
        area = None
        if area_code:
            area = Area.objects.filter(code=area_code).first()
            if area is None:
                raise Http404("Area nao encontrada.")
            try:
                ensure_area_access(request.user, area)
            except PermissionDenied:
                return Response({"detail": "Area nao autorizada."}, status=status.HTTP_403_FORBIDDEN)
        return Response(build_dashboard_payload(request.user, area=area))


class OfflineOutboxApiView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = OutboxBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created = []
        for item in serializer.validated_data["items"]:
            entry = enqueue_sync_item(
                entity_name=item["entity_name"],
                entity_id=item.get("entity_id"),
                action=item["action"],
                payload=item["payload"],
            )
            created.append(str(entry.id))
        return Response({"accepted": len(created), "ids": created}, status=status.HTTP_202_ACCEPTED)


class EquipmentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OccurrencePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class EquipmentListCreateApiView(APIView):
    pagination_class = EquipmentPagination

    def get(self, request, *args, **kwargs):
        ensure_permission(request.user, PermissionName.VIEW_AREA_DATA)
        queryset = base_equipment_queryset(request.user)
        area_code = request.query_params.get("area")
        if area_code:
            area = Area.objects.filter(code=area_code).first()
            if area is None:
                raise Http404("Area nao encontrada.")
            ensure_area_access(request.user, area)
        queryset = apply_equipment_filters(
            queryset,
            {
                "equipment_name": request.query_params.get("equipment_name", "") or request.query_params.get("search", ""),
                "tag_name": request.query_params.get("tag_name", ""),
                "area": area_code or "",
                "fabrica": request.query_params.get("fabrica", ""),
                "unidade": request.query_params.get("unidade", ""),
                "location": request.query_params.get("location", ""),
                "equipment_type": request.query_params.get("equipment_type", ""),
                "status": request.query_params.get("status", ""),
            },
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = EquipmentSummarySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        ensure_permission(request.user, PermissionName.MANAGE_AREA_DATA)
        serializer = EquipmentWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ensure_area_access(request.user, serializer.validated_data["area"])
        equipment = serializer.save()
        return Response(EquipmentDetailSerializer(equipment).data, status=status.HTTP_201_CREATED)


class EquipmentDetailApiView(APIView):
    def get_object(self, pk):
        equipment = Equipment.objects.select_related(
            "area",
            "unidade",
            "unidade__fabrica",
            "location",
            "location__unidade",
            "location__unidade__fabrica",
            "motor",
            "instrument",
        ).filter(pk=pk).first()
        if equipment is None:
            raise Http404("Equipamento nao encontrado.")
        return equipment

    def get(self, request, pk, *args, **kwargs):
        ensure_permission(request.user, PermissionName.VIEW_AREA_DATA)
        equipment = self.get_object(pk)
        ensure_area_access(request.user, equipment.area)
        return Response(EquipmentDetailSerializer(equipment).data)

    def patch(self, request, pk, *args, **kwargs):
        ensure_permission(request.user, PermissionName.MANAGE_AREA_DATA)
        equipment = self.get_object(pk)
        ensure_area_access(request.user, equipment.area)
        serializer = EquipmentWriteSerializer(equipment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        area = serializer.validated_data.get("area", equipment.area)
        ensure_area_access(request.user, area)
        equipment = serializer.save()
        return Response(EquipmentDetailSerializer(equipment).data)

    def put(self, request, pk, *args, **kwargs):
        return self.patch(request, pk, *args, **kwargs)


class EquipmentToggleStatusApiView(APIView):
    def post(self, request, pk, *args, **kwargs):
        ensure_permission(request.user, PermissionName.MANAGE_AREA_DATA)
        equipment = Equipment.objects.select_related("area").filter(pk=pk).first()
        if equipment is None:
            raise Http404("Equipamento nao encontrado.")
        ensure_area_access(request.user, equipment.area)
        toggle_equipment_active_state(equipment)
        return Response(EquipmentDetailSerializer(equipment).data)


class OccurrenceListCreateApiView(APIView):
    pagination_class = OccurrencePagination

    def get(self, request, *args, **kwargs):
        ensure_permission(request.user, PermissionName.VIEW_AREA_DATA)
        queryset = base_occurrence_queryset(request.user)
        area_code = request.query_params.get("area")
        if area_code:
            area = Area.objects.filter(code=area_code).first()
            if area is None:
                raise Http404("Area nao encontrada.")
            ensure_area_access(request.user, area)
        queryset = apply_occurrence_filters(
            queryset,
            {
                "search": request.query_params.get("search", ""),
                "area": area_code or "",
                "fabrica": request.query_params.get("fabrica", ""),
                "unidade": request.query_params.get("unidade", ""),
                "location": request.query_params.get("location", ""),
                "classification": request.query_params.get("classification", ""),
                "status": request.query_params.get("status", ""),
                "downtime": request.query_params.get("downtime", ""),
            },
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = OccurrenceSummarySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        ensure_permission(request.user, PermissionName.CREATE_OCCURRENCES)
        serializer = OccurrenceWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ensure_area_access(request.user, serializer.validated_data["area"])
        ensure_area_access(request.user, serializer.validated_data["equipment"].area)
        occurrence = create_occurrence_from_api(serializer.validated_data, request.user)
        return Response(OccurrenceDetailSerializer(occurrence).data, status=status.HTTP_201_CREATED)


class OccurrenceDetailApiView(APIView):
    def get_object(self, pk):
        occurrence = (
            Occurrence.objects.select_related(
                "equipment",
                "equipment__unidade",
                "equipment__unidade__fabrica",
                "area",
                "location",
                "location__unidade",
                "location__unidade__fabrica",
                "unidade",
                "unidade__fabrica",
                "responsible_collaborator",
                "reported_by_user",
            )
            .filter(pk=pk)
            .first()
        )
        if occurrence is None:
            raise Http404("Ocorrencia nao encontrada.")
        return occurrence

    def get(self, request, pk, *args, **kwargs):
        ensure_permission(request.user, PermissionName.VIEW_AREA_DATA)
        occurrence = self.get_object(pk)
        ensure_area_access(request.user, occurrence.area)
        return Response(OccurrenceDetailSerializer(occurrence).data)

    def patch(self, request, pk, *args, **kwargs):
        ensure_permission(request.user, PermissionName.EDIT_OCCURRENCES)
        occurrence = self.get_object(pk)
        ensure_area_access(request.user, occurrence.area)
        serializer = OccurrenceWriteSerializer(occurrence, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        area = serializer.validated_data.get("area", occurrence.area)
        ensure_area_access(request.user, area)
        if "equipment" in serializer.validated_data:
            ensure_area_access(request.user, serializer.validated_data["equipment"].area)
        occurrence = update_occurrence_from_api(occurrence, serializer.validated_data, request.user)
        return Response(OccurrenceDetailSerializer(occurrence).data)

    def put(self, request, pk, *args, **kwargs):
        return self.patch(request, pk, *args, **kwargs)


class OccurrenceStatusApiView(APIView):
    def post(self, request, pk, *args, **kwargs):
        ensure_permission(request.user, PermissionName.EDIT_OCCURRENCES)
        occurrence = Occurrence.objects.select_related("area", "equipment").filter(pk=pk).first()
        if occurrence is None:
            raise Http404("Ocorrencia nao encontrada.")
        ensure_area_access(request.user, occurrence.area)
        serializer = OccurrenceStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        occurrence = update_occurrence_status(
            occurrence,
            status=serializer.validated_data["status"],
            actor=request.user,
            note=serializer.validated_data.get("note", ""),
        )
        return Response(OccurrenceDetailSerializer(occurrence).data)
