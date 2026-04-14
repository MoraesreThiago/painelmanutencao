from fastapi import APIRouter

from app.routers.v1.endpoints import (
    areas,
    auth,
    burned_motor_records,
    collaborators,
    dashboard,
    equipments,
    external_service_orders,
    instruments,
    instrument_replacements,
    instrument_service_requests,
    locations,
    mechanical,
    motors,
    motor_replacements,
    notification_events,
    roles,
    users,
    movements,
)


router = APIRouter()
router.include_router(auth.router)
router.include_router(dashboard.router)
router.include_router(roles.router)
router.include_router(areas.router)
router.include_router(locations.router)
router.include_router(mechanical.router)
router.include_router(users.router)
router.include_router(collaborators.router)
router.include_router(equipments.router)
router.include_router(motors.router)
router.include_router(instruments.router)
router.include_router(movements.router)
router.include_router(motor_replacements.router)
router.include_router(burned_motor_records.router)
router.include_router(instrument_replacements.router)
router.include_router(instrument_service_requests.router)
router.include_router(external_service_orders.router)
router.include_router(notification_events.router)

