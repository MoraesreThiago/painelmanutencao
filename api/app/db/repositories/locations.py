from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.permissions import apply_area_scope
from app.models.location import Location
from app.models.user import User
from app.db.repositories.base import BaseRepository


class LocationRepository(BaseRepository[Location]):
    model = Location

    def list_visible(self, current_user: User) -> list[Location]:
        stmt = (
            apply_area_scope(select(Location), current_user, Location)
            .options(joinedload(Location.area))
            .order_by(Location.name)
        )
        return self.list(statement=stmt)

