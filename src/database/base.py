"""
Base declarativa para modelos de SQLAlchemy
"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func
from datetime import datetime
from typing import Optional

class Base(DeclarativeBase):
    """
    Clase base para todos los modelos de la base de datos

    Incluye campos comunes como timestamps
    """
    pass

class TimestampMixin:
    """
    Mixin para agregar timestamps automáticos a los modelos
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )
