from __future__ import annotations

from sqlalchemy import select

from app.core.enums import AreaCode
from app.core.permissions import apply_area_id_scope
from app.models.area import Area
from app.models.user import User
from app.db.repositories.base import BaseRepository


class AreaRepository(BaseRepository[Area]):
    model = Area

    def get_by_code(self, code: AreaCode) -> Area | None:
        stmt = select(Area).where(Area.code == code)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_visible(self, current_user: User) -> list[Area]:
        stmt = apply_area_id_scope(select(Area), current_user, Area.id).order_by(Area.name)
        return self.list(statement=stmt)

