from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import MetaData, String
from sqlalchemy.types import TypeDecorator, UserDefinedType
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class PGVector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_: Any) -> str:
        return f"VECTOR({self.dimensions})"

    def bind_processor(self, _dialect: Any):
        def process(value: list[float] | None) -> str | None:
            if value is None:
                return None
            return "[" + ",".join(str(float(v)) for v in value) + "]"

        return process

    def result_processor(self, _dialect: Any, _coltype: Any):
        def process(value: Any) -> list[float] | None:
            if value is None:
                return None
            if isinstance(value, list):
                return [float(v) for v in value]
            raw = str(value).strip("[] ")
            return [] if not raw else [float(v) for v in raw.split(",")]

        return process


class Vector512(TypeDecorator[list[float]]):
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return PGVector(512)
        return super().load_dialect_impl(dialect)
