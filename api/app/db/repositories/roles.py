from __future__ import annotations

from sqlalchemy import select

from app.core.enums import RoleName
from app.core.permissions import ACTIVE_ROLE_NAMES
from app.models.role import Role
from app.db.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    model = Role

    def get_by_name(self, name: RoleName) -> Role | None:
        stmt = select(Role).where(Role.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[Role]:
        stmt = select(Role).where(Role.name.in_(ACTIVE_ROLE_NAMES)).order_by(Role.name)
        return self.list(statement=stmt)

