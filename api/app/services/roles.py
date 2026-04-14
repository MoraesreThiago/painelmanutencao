from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.repositories.roles import RoleRepository


class RoleService:
    def __init__(self, db: Session):
        self.repository = RoleRepository(db)

    def list_roles(self):
        return self.repository.list_all()

