from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload, selectinload

from app.core.permissions import get_user_area_ids, is_global_user
from app.models.user import User
from app.models.user_area import UserArea
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get(self, entity_id) -> User | None:
        stmt = (
            select(User)
            .where(User.id == entity_id)
            .options(
                joinedload(User.area),
                selectinload(User.allowed_areas),
                selectinload(User.area_assignments),
                joinedload(User.role),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str) -> User | None:
        stmt = (
            select(User)
            .where(User.email == email)
            .options(
                joinedload(User.area),
                selectinload(User.allowed_areas),
                selectinload(User.area_assignments),
                joinedload(User.role),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_visible(self, current_user: User) -> list[User]:
        stmt = (
            select(User)
            .options(
                joinedload(User.area),
                selectinload(User.allowed_areas),
                selectinload(User.area_assignments),
                joinedload(User.role),
            )
            .order_by(User.full_name)
        )
        if not is_global_user(current_user):
            area_ids = get_user_area_ids(current_user)
            if not area_ids:
                return []
            stmt = (
                stmt.outerjoin(User.area_assignments)
                .where(
                    or_(
                        User.area_id.in_(area_ids),
                        UserArea.area_id.in_(area_ids),
                    )
                )
                .distinct()
            )
        return self.list(statement=stmt)

