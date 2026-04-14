from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.db.database import SessionLocal
from app.core.security import get_password_hash
from app.core.enums import (
    AreaCode,
    EquipmentStatus,
    EquipmentType,
    InstrumentStatus,
    MotorStatus,
    RecordStatus,
    RoleName,
)
from app.models.area import Area
from app.models.collaborator import Collaborator
from app.models.equipment import Equipment
from app.models.instrument import Instrument
from app.models.location import Location
from app.models.motor import Motor
from app.models.role import Role
from app.models.user import User


def seed_initial_data() -> None:
    with SessionLocal() as db:
        def ensure_equipment(*, code: str, defaults: dict) -> Equipment:
            equipment = db.execute(select(Equipment).where(Equipment.code == code)).scalar_one_or_none()
            if equipment:
                for key, value in defaults.items():
                    setattr(equipment, key, value)
                db.add(equipment)
                db.flush()
                return equipment
            equipment = Equipment(code=code, **defaults)
            db.add(equipment)
            db.flush()
            return equipment

        def ensure_motor(*, code: str, equipment_defaults: dict, motor_defaults: dict) -> Motor:
            equipment = ensure_equipment(code=code, defaults=equipment_defaults)
            motor = db.execute(select(Motor).where(Motor.equipment_id == equipment.id)).scalar_one_or_none()
            if motor:
                for key, value in motor_defaults.items():
                    setattr(motor, key, value)
                db.add(motor)
                db.flush()
                return motor
            motor = Motor(equipment_id=equipment.id, **motor_defaults)
            db.add(motor)
            db.flush()
            return motor

        def ensure_instrument(*, code: str, equipment_defaults: dict, instrument_defaults: dict) -> Instrument:
            equipment = ensure_equipment(code=code, defaults=equipment_defaults)
            instrument = db.execute(select(Instrument).where(Instrument.equipment_id == equipment.id)).scalar_one_or_none()
            if instrument:
                for key, value in instrument_defaults.items():
                    setattr(instrument, key, value)
                db.add(instrument)
                db.flush()
                return instrument
            instrument = Instrument(equipment_id=equipment.id, **instrument_defaults)
            db.add(instrument)
            db.flush()
            return instrument

        roles = {}
        for role_name in RoleName:
            role = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
            if not role:
                role = Role(name=role_name, description=f"{role_name.value} role")
                db.add(role)
                db.flush()
            roles[role_name] = role

        area_specs = [
            ("Eletrica", AreaCode.ELETRICA, "Area eletrica da manutencao"),
            ("Mecanica", AreaCode.MECANICA, "Area mecanica da manutencao"),
            ("Instrumentacao", AreaCode.INSTRUMENTACAO, "Area de instrumentacao"),
        ]
        areas = {}
        for name, code, description in area_specs:
            area = db.execute(select(Area).where(Area.code == code)).scalar_one_or_none()
            if not area:
                area = Area(name=name, code=code, description=description)
                db.add(area)
                db.flush()
            areas[code] = area

        location_specs = [
            ("Subestacao Principal", "Utilidades", AreaCode.ELETRICA),
            ("Oficina Mecanica", "Manutencao", AreaCode.MECANICA),
            ("Laboratorio de Calibracao", "Instrumentacao", AreaCode.INSTRUMENTACAO),
        ]
        locations = {}
        for name, sector, area_code in location_specs:
            stmt = (
                select(Location)
                .where(Location.name == name)
                .where(Location.sector == sector)
                .where(Location.area_id == areas[area_code].id)
            )
            location = db.execute(stmt).scalar_one_or_none()
            if not location:
                location = Location(
                    name=name,
                    sector=sector,
                    area_id=areas[area_code].id,
                    description=f"Local inicial para {area_code.value.lower()}",
                )
                db.add(location)
                db.flush()
            locations[area_code] = location

        admin = db.execute(select(User).where(User.email == settings.default_admin_email)).scalar_one_or_none()
        if not admin:
            admin = User(
                full_name="Administrador da Plataforma",
                email=str(settings.default_admin_email),
                registration_number="ADM-0001",
                job_title="Administrador",
                phone="+55 11 99999-9999",
                password_hash=get_password_hash(settings.default_admin_password),
                is_active=True,
                role_id=roles[RoleName.ADMIN].id,
                area_id=None,
            )
            db.add(admin)
            db.flush()

        has_collaborators = db.execute(select(Collaborator.id).limit(1)).first()
        if not has_collaborators:
            db.add_all(
                [
                    Collaborator(
                        full_name="Carlos Eletricista",
                        registration_number="COL-E-001",
                        job_title="Tecnico Eletrico",
                        contact_phone="+55 11 90000-1001",
                        status=RecordStatus.ACTIVE,
                        area_id=areas[AreaCode.ELETRICA].id,
                    ),
                    Collaborator(
                        full_name="Marina Mecanica",
                        registration_number="COL-M-001",
                        job_title="Tecnica Mecanica",
                        contact_phone="+55 11 90000-1002",
                        status=RecordStatus.ACTIVE,
                        area_id=areas[AreaCode.MECANICA].id,
                    ),
                    Collaborator(
                        full_name="Rafael Instrumentista",
                        registration_number="COL-I-001",
                        job_title="Tecnico de Instrumentacao",
                        contact_phone="+55 11 90000-1003",
                        status=RecordStatus.ACTIVE,
                        area_id=areas[AreaCode.INSTRUMENTACAO].id,
                    ),
                ],
            )
            db.flush()

        ensure_equipment(
            code="EQ-MEC-001",
            defaults={
                "tag": "P-1001",
                "description": "Bomba de processo 01",
                "sector": "Manutencao",
                "manufacturer": "FlowTech",
                "model": "PX-200",
                "serial_number": "FT-2026-001",
                "notes": "Equipamento inicial para testes.",
                "type": EquipmentType.GENERIC,
                "status": EquipmentStatus.ACTIVE,
                "registered_at": datetime.now(UTC),
                "area_id": areas[AreaCode.MECANICA].id,
                "location_id": locations[AreaCode.MECANICA].id,
            },
        )

        ensure_equipment(
            code="EQ-E-001",
            defaults={
                "tag": "TH-13405",
                "description": "Transportador horizontal da linha 13",
                "sector": "Utilidades",
                "manufacturer": "ProcessTech",
                "model": "TH-13",
                "serial_number": "PTH-2026-1305",
                "notes": "Equipamento alvo para testes de troca de motor.",
                "type": EquipmentType.GENERIC,
                "status": EquipmentStatus.ACTIVE,
                "registered_at": datetime.now(UTC),
                "area_id": areas[AreaCode.ELETRICA].id,
                "location_id": locations[AreaCode.ELETRICA].id,
            },
        )

        ensure_motor(
            code="MTR-E-001",
            equipment_defaults={
                "tag": "MO215",
                "description": "Motor da correia transportadora 01",
                "sector": "Utilidades",
                "manufacturer": "WEG",
                "model": "W22",
                "serial_number": "WEG-2026-1001",
                "notes": "Motor em operacao para testes de troca.",
                "type": EquipmentType.MOTOR,
                "status": EquipmentStatus.ACTIVE,
                "registered_at": datetime.now(UTC),
                "area_id": areas[AreaCode.ELETRICA].id,
                "location_id": locations[AreaCode.ELETRICA].id,
            },
            motor_defaults={
                "unique_identifier": "MO215",
                "current_status": MotorStatus.IN_OPERATION,
                "last_internal_service_at": (datetime.now(UTC) - timedelta(days=45)).date(),
            },
        )

        ensure_motor(
            code="MTR-E-002",
            equipment_defaults={
                "tag": "MO145",
                "description": "Motor reserva do almoxarifado eletrico",
                "sector": "Utilidades",
                "manufacturer": "WEG",
                "model": "W22",
                "serial_number": "WEG-2026-1002",
                "notes": "Motor reserva para testes de troca.",
                "type": EquipmentType.MOTOR,
                "status": EquipmentStatus.ACTIVE,
                "registered_at": datetime.now(UTC),
                "area_id": areas[AreaCode.ELETRICA].id,
                "location_id": locations[AreaCode.ELETRICA].id,
            },
            motor_defaults={
                "unique_identifier": "MO145",
                "current_status": MotorStatus.RESERVE,
                "last_internal_service_at": (datetime.now(UTC) - timedelta(days=20)).date(),
            },
        )

        ensure_equipment(
            code="EQ-I-001",
            defaults={
                "tag": "FT-2203",
                "description": "Linha de vazao do tanque 22",
                "sector": "Instrumentacao",
                "manufacturer": "ProcessTech",
                "model": "FT-2200",
                "serial_number": "FTI-2026-2203",
                "notes": "Equipamento alvo para testes de troca de instrumento.",
                "type": EquipmentType.GENERIC,
                "status": EquipmentStatus.ACTIVE,
                "registered_at": datetime.now(UTC),
                "area_id": areas[AreaCode.INSTRUMENTACAO].id,
                "location_id": locations[AreaCode.INSTRUMENTACAO].id,
            },
        )

        ensure_instrument(
            code="INS-I-001",
            equipment_defaults={
                "tag": "PT-9001",
                "description": "Transmissor de pressao linha B",
                "sector": "Instrumentacao",
                "manufacturer": "Emerson",
                "model": "3051",
                "serial_number": "EMR-2026-5001",
                "notes": "Instrumento em campo para testes de troca.",
                "type": EquipmentType.INSTRUMENT,
                "status": EquipmentStatus.ACTIVE,
                "registered_at": datetime.now(UTC),
                "area_id": areas[AreaCode.INSTRUMENTACAO].id,
                "location_id": locations[AreaCode.INSTRUMENTACAO].id,
            },
            instrument_defaults={
                "unique_identifier": "PT9001",
                "instrument_type": "Pressure Transmitter",
                "current_status": InstrumentStatus.INSTALLED,
                "calibration_due_date": (datetime.now(UTC) + timedelta(days=15)).date(),
            },
        )

        ensure_instrument(
            code="INS-I-002",
            equipment_defaults={
                "tag": "PT-9002",
                "description": "Transmissor de pressao reserva",
                "sector": "Instrumentacao",
                "manufacturer": "Emerson",
                "model": "3051",
                "serial_number": "EMR-2026-5002",
                "notes": "Instrumento reserva para testes de troca.",
                "type": EquipmentType.INSTRUMENT,
                "status": EquipmentStatus.ACTIVE,
                "registered_at": datetime.now(UTC),
                "area_id": areas[AreaCode.INSTRUMENTACAO].id,
                "location_id": locations[AreaCode.INSTRUMENTACAO].id,
            },
            instrument_defaults={
                "unique_identifier": "PT9002",
                "instrument_type": "Pressure Transmitter",
                "current_status": InstrumentStatus.IN_STOCK,
                "calibration_due_date": (datetime.now(UTC) + timedelta(days=45)).date(),
            },
        )

        db.commit()


if __name__ == "__main__":
    seed_initial_data()

