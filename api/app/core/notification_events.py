from __future__ import annotations

from enum import Enum


class NotificationEventType(str, Enum):
    MOVEMENT_RECORDED = "movement.recorded"
    MOTOR_CREATED = "motor.created"
    MOTOR_REPLACED = "motor.replaced"
    MOTOR_BURNED_RECORDED = "motor.burned_recorded"
    MOTOR_BURNED_STATUS_CHANGED = "motor.burned_status_changed"
    MOTOR_SENT_EXTERNAL_SERVICE = "motor.sent_external_service"
    MOTOR_RETURNED_EXTERNAL_SERVICE = "motor.returned_external_service"
    INSTRUMENT_CREATED = "instrument.created"
    INSTRUMENT_REPLACED = "instrument.replaced"
    INSTRUMENT_SERVICE_REQUESTED = "instrument.service_requested"
    INSTRUMENT_SERVICE_COMPLETED = "instrument.service_completed"
