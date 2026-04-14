from app.db.base import Base

from .area import Area
from .audit_log import AuditLog
from .burned_motor_record import BurnedMotorRecord
from .collaborator import Collaborator
from .equipment import Equipment
from .external_service_order import ExternalServiceOrder
from .instrument import Instrument
from .instrument_replacement import InstrumentReplacement
from .instrument_service_request import InstrumentServiceRequest
from .location import Location
from .motor import Motor
from .motor_replacement import MotorReplacement
from .movement import Movement
from .notification_event import NotificationEvent
from .role import Role
from .user import User
from .user_area import UserArea

__all__ = [
    "Area",
    "AuditLog",
    "Base",
    "BurnedMotorRecord",
    "Collaborator",
    "Equipment",
    "ExternalServiceOrder",
    "Instrument",
    "InstrumentReplacement",
    "InstrumentServiceRequest",
    "Location",
    "Motor",
    "MotorReplacement",
    "Movement",
    "NotificationEvent",
    "Role",
    "User",
    "UserArea",
]
