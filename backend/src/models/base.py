"""
Base models and mixins for database entities.
Provides common functionality for all models.
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Boolean, Integer, func, MetaData
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs

# Define naming conventions for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""
    metadata = metadata
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        name = cls.__name__
        # Convert CamelCase to snake_case
        result = []
        for i, char in enumerate(name):
            if i > 0 and char.isupper() and name[i-1].islower():
                result.append("_")
            result.append(char.lower())
        return "".join(result)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class TimestampMixin:
    """Mixin for adding timestamp fields."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    
    def soft_delete(self) -> None:
        """Mark entity as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore soft deleted entity."""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """Mixin for audit fields."""
    
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )
    
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )