from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.base import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, db: Session):
        self.db = db

    def get(self, entity_id) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == entity_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(
        self,
        *,
        statement: Select | None = None,
        limit: int | None = None,
        offset: int = 0,
        unique_results: bool = False,
    ) -> list[ModelType]:
        stmt = statement if statement is not None else select(self.model)
        if offset:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = self.db.execute(stmt)
        if unique_results:
            result = result.unique()
        return list(result.scalars().all())

    def create(self, data: dict) -> ModelType:
        instance = self.model(**data)
        self.db.add(instance)
        self.db.flush()
        return instance

    def update(self, instance: ModelType, data: dict) -> ModelType:
        for key, value in data.items():
            setattr(instance, key, value)
        self.db.add(instance)
        self.db.flush()
        return instance

    def delete(self, instance: ModelType) -> None:
        self.db.delete(instance)
        self.db.flush()
