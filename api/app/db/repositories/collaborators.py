from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.permissions import apply_area_scope
from app.models.collaborator import Collaborator
from app.models.user import User
from app.db.repositories.base import BaseRepository


class CollaboratorRepository(BaseRepository[Collaborator]):
    model = Collaborator

    def get(self, entity_id) -> Collaborator | None:
        stmt = (
            select(Collaborator)
            .where(Collaborator.id == entity_id)
            .options(joinedload(Collaborator.area), joinedload(Collaborator.linked_user))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_visible(self, current_user: User) -> list[Collaborator]:
        stmt = (
            apply_area_scope(select(Collaborator), current_user, Collaborator)
            .options(joinedload(Collaborator.area), joinedload(Collaborator.linked_user))
            .order_by(Collaborator.full_name)
        )
        return self.list(statement=stmt)

