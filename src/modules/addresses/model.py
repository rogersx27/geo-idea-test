"""
Modelo de direcciones con geolocalización
"""
from typing import Optional
from sqlalchemy import String, Integer, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.database.base import Base, TimestampMixin


class Address(Base, TimestampMixin):
    """
    Modelo de direcciones con coordenadas geográficas

    Attributes:
        id: Identificador único
        hash: Hash único de la dirección (16 caracteres)
        number: Número de la calle
        street: Nombre de la calle
        unit: Unidad/Departamento
        city: Ciudad
        district: Distrito/Comuna
        region: Región/Estado (código de 10 caracteres)
        postcode: Código postal
        external_id: ID externo (20 caracteres)
        accuracy: Nivel de precisión de las coordenadas
        longitude: Longitud (coordenada X)
        latitude: Latitud (coordenada Y)
        created_at: Fecha de creación (automático)
        updated_at: Fecha de última actualización (automático)
    """

    __tablename__ = "addresses"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Hash único
    hash: Mapped[Optional[str]] = mapped_column(
        String(16), unique=True, nullable=True, index=True
    )

    # Campos de dirección
    number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    street: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    postcode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    accuracy: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Coordenadas geográficas (DECIMAL(10, 7))
    longitude: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 7), nullable=True, comment="Longitud (coordenada X)"
    )
    latitude: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 7), nullable=True, comment="Latitud (coordenada Y)"
    )

    # Índices compuestos (los índices simples ya están en las columnas)
    __table_args__ = (
        # Índice para búsqueda por coordenadas
        Index("idx_addresses_coords", "longitude", "latitude"),
        # Índice para búsqueda de dirección completa
        Index("idx_addresses_full", "city", "street", "number"),
        # Índice adicional por ciudad
        Index("idx_addresses_city", "city"),
        # Índice por calle
        Index("idx_addresses_street", "street"),
        # Índice por región
        Index("idx_addresses_region", "region"),
    )

    def __repr__(self) -> str:
        """Representación string del modelo"""
        address_parts = []
        if self.street:
            address_parts.append(self.street)
        if self.number:
            address_parts.append(self.number)
        if self.city:
            address_parts.append(self.city)

        address_str = ", ".join(address_parts) if address_parts else "No address"
        return f"<Address(id={self.id}, hash='{self.hash}', address='{address_str}')>"

    def to_dict(self) -> dict:
        """
        Convierte el modelo a diccionario

        Returns:
            dict: Diccionario con todos los campos del modelo
        """
        return {
            "id": self.id,
            "hash": self.hash,
            "number": self.number,
            "street": self.street,
            "unit": self.unit,
            "city": self.city,
            "district": self.district,
            "region": self.region,
            "postcode": self.postcode,
            "external_id": self.external_id,
            "accuracy": self.accuracy,
            "longitude": float(self.longitude) if self.longitude else None,
            "latitude": float(self.latitude) if self.latitude else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def full_address(self) -> str:
        """
        Genera la dirección completa como string

        Returns:
            str: Dirección formateada
        """
        parts = []
        if self.street:
            parts.append(self.street)
        if self.number:
            parts.append(self.number)
        if self.unit:
            parts.append(f"Unit {self.unit}")
        if self.city:
            parts.append(self.city)
        if self.region:
            parts.append(self.region)
        if self.postcode:
            parts.append(self.postcode)

        return ", ".join(parts) if parts else ""

    @property
    def coordinates(self) -> Optional[tuple[float, float]]:
        """
        Retorna las coordenadas como tupla (longitude, latitude)

        Returns:
            Optional[tuple[float, float]]: Coordenadas o None si no están disponibles
        """
        if self.longitude is not None and self.latitude is not None:
            return (float(self.longitude), float(self.latitude))
        return None
