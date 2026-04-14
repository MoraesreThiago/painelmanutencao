from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import AreaCode, InstrumentServiceStatus, InstrumentServiceType, InstrumentStatus
from app.core.notification_events import NotificationEventType
from app.core.permissions import PermissionName, ensure_area_access, ensure_permission, ensure_permission_in_area
from app.db.repositories.instrument_replacements import InstrumentReplacementRepository
from app.db.repositories.instrument_service_requests import InstrumentServiceRequestRepository
from app.db.repositories.instruments import InstrumentRepository
from app.services.audit import AuditService
from app.services.notification import NotificationService
from app.services.trackable_history import TrackableHistoryService


class InstrumentServiceRequestService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = InstrumentServiceRequestRepository(db)
        self.instrument_repository = InstrumentRepository(db)
        self.instrument_replacement_repository = InstrumentReplacementRepository(db)
        self.audit_service = AuditService(db)
        self.notification_service = NotificationService(db)
        self.history_service = TrackableHistoryService(db)

    def list_requests(self, current_user):
        ensure_permission(current_user, PermissionName.VIEW_AREA_DATA)
        return self.repository.list_visible(current_user)

    def get_request(self, request_id, actor):
        request = self.repository.get(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instrument service request not found.",
            )
        ensure_permission_in_area(actor, PermissionName.VIEW_AREA_DATA, request.area_id)
        return request

    def create_request(self, data, actor):
        instrument = self.instrument_repository.get(data.instrument_id)
        if not instrument:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found.")
        self._ensure_instrumentation_item(instrument)
        ensure_permission_in_area(actor, PermissionName.CREATE_OCCURRENCES, instrument.equipment.area_id)

        if data.instrument_replacement_id:
            replacement = self.instrument_replacement_repository.get(data.instrument_replacement_id)
            if not replacement:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Instrument replacement not found.",
                )
            ensure_area_access(actor, replacement.area_id)

        requested_at = data.requested_at or datetime.now(UTC)
        payload = data.model_dump()
        payload["area_id"] = instrument.equipment.area_id
        payload["registered_by_user_id"] = actor.id
        payload["requested_at"] = requested_at
        request = self.repository.create(payload)

        status_after = self._instrument_status_for_request(
            request.service_type,
            request.service_status,
            request.actual_return_at,
        )
        self.history_service.record_event(
            equipment=instrument.equipment,
            actor=actor,
            reason=f"Solicitacao de {request.service_type.value} registrada para o instrumento.",
            status_after=status_after.value,
            notes=request.notes or request.reason,
            moved_at=requested_at,
        )

        self.audit_service.record(
            actor=actor,
            entity_name="InstrumentServiceRequest",
            entity_id=str(request.id),
            action="created",
            area_id=request.area_id,
            summary=f"Solicitacao de servico criada para {instrument.unique_identifier}.",
            payload=payload,
        )
        self.notification_service.enqueue(
            event_type=NotificationEventType.INSTRUMENT_SERVICE_REQUESTED,
            entity_name="InstrumentServiceRequest",
            entity_id=str(request.id),
            area_id=request.area_id,
            payload={
                "instrument": instrument.unique_identifier,
                "service_type": request.service_type.value,
                "service_status": request.service_status.value,
            },
        )
        self.db.commit()
        return self.repository.get(request.id)

    def update_request(self, request_id, data, actor):
        request = self.get_request(request_id, actor)
        ensure_permission_in_area(actor, PermissionName.EDIT_OCCURRENCES, request.area_id)
        payload = data.model_dump(exclude_unset=True)
        updated = self.repository.update(request, payload)

        status_after = self._instrument_status_for_request(
            updated.service_type,
            updated.service_status,
            updated.actual_return_at,
        )
        updated.instrument.current_status = status_after
        updated.instrument.equipment.status = self.history_service.equipment_service.map_trackable_status_to_equipment_status(
            status_after.value,
        )

        if updated.service_status == InstrumentServiceStatus.COMPLETED:
            self.notification_service.enqueue(
                event_type=NotificationEventType.INSTRUMENT_SERVICE_COMPLETED,
                entity_name="InstrumentServiceRequest",
                entity_id=str(updated.id),
                area_id=updated.area_id,
                payload={
                    "instrument": updated.instrument.unique_identifier,
                    "actual_return_at": updated.actual_return_at,
                },
            )

        self.audit_service.record(
            actor=actor,
            entity_name="InstrumentServiceRequest",
            entity_id=str(updated.id),
            action="updated",
            area_id=updated.area_id,
            summary=f"Solicitacao de servico do instrumento {updated.instrument.unique_identifier} atualizada.",
            payload=payload,
        )
        self.db.commit()
        return self.repository.get(updated.id)

    @staticmethod
    def _instrument_status_for_request(
        service_type: InstrumentServiceType,
        service_status: InstrumentServiceStatus,
        actual_return_at,
    ) -> InstrumentStatus:
        if service_status in {InstrumentServiceStatus.COMPLETED, InstrumentServiceStatus.CANCELLED}:
            return InstrumentStatus.IN_STOCK
        if service_type == InstrumentServiceType.CALIBRATION:
            return InstrumentStatus.IN_CALIBRATION
        return InstrumentStatus.IN_MAINTENANCE

    @staticmethod
    def _ensure_instrumentation_item(instrument) -> None:
        if instrument.equipment.area.code != AreaCode.INSTRUMENTACAO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instrument service flow is only available for the instrumentation area.",
            )

