"""
Tests para el modelo Address
"""
import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.modules.addresses.model import Address


@pytest.mark.database
@pytest.mark.asyncio
class TestAddressModel:
    """Tests básicos del modelo Address"""

    async def test_create_address_minimal(self, db_session: AsyncSession):
        """Test crear dirección con campos mínimos"""
        address = Address(
            street="Main Street",
            number="123",
            city="Santiago",
        )
        db_session.add(address)
        await db_session.commit()
        await db_session.refresh(address)

        assert address.id is not None
        assert address.street == "Main Street"
        assert address.number == "123"
        assert address.city == "Santiago"
        assert address.created_at is not None
        assert isinstance(address.created_at, datetime)

    async def test_create_address_full(self, db_session: AsyncSession):
        """Test crear dirección con todos los campos"""
        address = Address(
            hash="abc123def456",
            number="456",
            street="Avenida Libertador",
            unit="Depto 301",
            city="Providencia",
            district="Providencia",
            region="RM",
            postcode="7500000",
            external_id="EXT001",
            accuracy="ROOFTOP",
            longitude=Decimal("-70.6506"),
            latitude=Decimal("-33.4372"),
        )
        db_session.add(address)
        await db_session.commit()
        await db_session.refresh(address)

        assert address.id is not None
        assert address.hash == "abc123def456"
        assert address.number == "456"
        assert address.street == "Avenida Libertador"
        assert address.unit == "Depto 301"
        assert address.city == "Providencia"
        assert address.district == "Providencia"
        assert address.region == "RM"
        assert address.postcode == "7500000"
        assert address.external_id == "EXT001"
        assert address.accuracy == "ROOFTOP"
        assert float(address.longitude) == -70.6506
        assert float(address.latitude) == -33.4372

    async def test_hash_unique_constraint(self, db_session: AsyncSession):
        """Test que el hash debe ser único"""
        # Crear primera dirección
        address1 = Address(hash="unique123", street="Street 1", city="City 1")
        db_session.add(address1)
        await db_session.commit()

        # Intentar crear segunda con mismo hash
        address2 = Address(hash="unique123", street="Street 2", city="City 2")
        db_session.add(address2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_coordinates_precision(self, db_session: AsyncSession):
        """Test que las coordenadas mantienen la precisión DECIMAL(10,7)"""
        address = Address(
            street="Test Street",
            city="Test City",
            longitude=Decimal("-70.6506123"),
            latitude=Decimal("-33.4372456"),
        )
        db_session.add(address)
        await db_session.commit()
        await db_session.refresh(address)

        # Verificar que se mantiene la precisión de 7 decimales
        assert str(address.longitude) == "-70.6506123"
        assert str(address.latitude) == "-33.4372456"

    async def test_timestamps_auto_created(self, db_session: AsyncSession):
        """Test que created_at se crea automáticamente"""
        address = Address(street="Test", city="Test")
        db_session.add(address)
        await db_session.commit()
        await db_session.refresh(address)

        assert address.created_at is not None
        assert isinstance(address.created_at, datetime)
        # updated_at puede ser None si no se ha actualizado
        assert address.updated_at is None or isinstance(address.updated_at, datetime)


@pytest.mark.database
@pytest.mark.asyncio
class TestAddressCRUD:
    """Tests de operaciones CRUD en Address"""

    async def test_read_address(self, db_session: AsyncSession):
        """Test leer una dirección por ID"""
        # Crear
        address = Address(street="Read Street", city="Read City", number="100")
        db_session.add(address)
        await db_session.commit()
        address_id = address.id

        # Leer en nueva sesión
        result = await db_session.execute(select(Address).where(Address.id == address_id))
        found_address = result.scalar_one()

        assert found_address.id == address_id
        assert found_address.street == "Read Street"
        assert found_address.city == "Read City"

    async def test_update_address(self, db_session: AsyncSession):
        """Test actualizar una dirección"""
        # Crear
        address = Address(street="Old Street", city="Old City")
        db_session.add(address)
        await db_session.commit()
        await db_session.refresh(address)

        # Actualizar
        address.street = "New Street"
        address.city = "New City"
        await db_session.commit()
        await db_session.refresh(address)

        assert address.street == "New Street"
        assert address.city == "New City"
        # updated_at debería actualizarse
        assert address.updated_at is not None

    async def test_delete_address(self, db_session: AsyncSession):
        """Test eliminar una dirección"""
        # Crear
        address = Address(street="Delete Street", city="Delete City")
        db_session.add(address)
        await db_session.commit()
        address_id = address.id

        # Eliminar
        await db_session.delete(address)
        await db_session.commit()

        # Verificar que no existe
        result = await db_session.execute(select(Address).where(Address.id == address_id))
        assert result.scalar_one_or_none() is None

    async def test_bulk_insert(self, db_session: AsyncSession):
        """Test inserción masiva de direcciones"""
        addresses = [
            Address(street=f"Street {i}", city=f"City {i}", number=str(i))
            for i in range(1, 11)
        ]
        db_session.add_all(addresses)
        await db_session.commit()

        # Verificar que se insertaron todas
        result = await db_session.execute(select(func.count(Address.id)))
        count = result.scalar()
        assert count >= 10


@pytest.mark.database
@pytest.mark.asyncio
class TestAddressQueries:
    """Tests de búsquedas y queries en Address"""

    async def test_find_by_city(self, db_session: AsyncSession):
        """Test buscar direcciones por ciudad (usa índice idx_addresses_city)"""
        # Crear direcciones en diferentes ciudades
        addresses = [
            Address(street="Street 1", city="Santiago", number="100"),
            Address(street="Street 2", city="Santiago", number="200"),
            Address(street="Street 3", city="Valparaíso", number="300"),
        ]
        db_session.add_all(addresses)
        await db_session.commit()

        # Buscar por ciudad
        result = await db_session.execute(
            select(Address).where(Address.city == "Santiago")
        )
        santiago_addresses = result.scalars().all()

        assert len(santiago_addresses) >= 2
        assert all(addr.city == "Santiago" for addr in santiago_addresses)

    async def test_find_by_street(self, db_session: AsyncSession):
        """Test buscar por calle (usa índice idx_addresses_street)"""
        address = Address(street="Unique Street Name", city="Test City", number="1")
        db_session.add(address)
        await db_session.commit()

        # Buscar
        result = await db_session.execute(
            select(Address).where(Address.street == "Unique Street Name")
        )
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.street == "Unique Street Name"

    async def test_find_by_region(self, db_session: AsyncSession):
        """Test buscar por región (usa índice idx_addresses_region)"""
        addresses = [
            Address(street="Street A", city="City A", region="RM"),
            Address(street="Street B", city="City B", region="RM"),
            Address(street="Street C", city="City C", region="V"),
        ]
        db_session.add_all(addresses)
        await db_session.commit()

        # Buscar
        result = await db_session.execute(select(Address).where(Address.region == "RM"))
        rm_addresses = result.scalars().all()

        assert len(rm_addresses) >= 2
        assert all(addr.region == "RM" for addr in rm_addresses)

    async def test_find_by_full_address(self, db_session: AsyncSession):
        """Test buscar por dirección completa (usa índice idx_addresses_full)"""
        address = Address(
            street="Test Street", city="Test City", number="123", region="RM"
        )
        db_session.add(address)
        await db_session.commit()

        # Buscar con los 3 campos del índice compuesto
        result = await db_session.execute(
            select(Address).where(
                Address.city == "Test City",
                Address.street == "Test Street",
                Address.number == "123",
            )
        )
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.street == "Test Street"
        assert found.city == "Test City"
        assert found.number == "123"

    async def test_find_by_coordinates(self, db_session: AsyncSession):
        """Test buscar por coordenadas (usa índice idx_addresses_coords)"""
        # Usar coordenadas únicas con más decimales para evitar colisiones
        import random
        unique_offset = random.randint(1, 9999)
        unique_lng = Decimal(f"-70.{unique_offset:04d}123")
        unique_lat = Decimal(f"-33.{unique_offset:04d}456")

        address = Address(
            street="Geo Street",
            city="Geo City",
            longitude=unique_lng,
            latitude=unique_lat,
        )
        db_session.add(address)
        await db_session.commit()

        # Buscar por coordenadas exactas
        result = await db_session.execute(
            select(Address).where(
                Address.longitude == unique_lng,
                Address.latitude == unique_lat,
            )
        )
        found = result.scalars().first()

        assert found is not None
        assert found.longitude == unique_lng
        assert found.latitude == unique_lat

    async def test_find_by_hash(self, db_session: AsyncSession):
        """Test buscar por hash (índice único)"""
        address = Address(hash="findme123", street="Hash Street", city="Hash City")
        db_session.add(address)
        await db_session.commit()

        # Buscar
        result = await db_session.execute(select(Address).where(Address.hash == "findme123"))
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.hash == "findme123"


@pytest.mark.database
@pytest.mark.asyncio
class TestAddressMethods:
    """Tests de métodos y propiedades del modelo Address"""

    async def test_to_dict_method(self, db_session: AsyncSession):
        """Test método to_dict()"""
        address = Address(
            hash="dict123",
            street="Dict Street",
            number="456",
            city="Dict City",
            region="RM",
            longitude=Decimal("-70.6506"),
            latitude=Decimal("-33.4372"),
        )
        db_session.add(address)
        await db_session.commit()
        await db_session.refresh(address)

        address_dict = address.to_dict()

        assert isinstance(address_dict, dict)
        assert address_dict["hash"] == "dict123"
        assert address_dict["street"] == "Dict Street"
        assert address_dict["number"] == "456"
        assert address_dict["city"] == "Dict City"
        assert address_dict["region"] == "RM"
        assert address_dict["longitude"] == -70.6506
        assert address_dict["latitude"] == -33.4372
        assert "created_at" in address_dict
        assert "updated_at" in address_dict

    def test_full_address_property(self):
        """Test propiedad full_address"""
        address = Address(
            street="Main Street",
            number="123",
            unit="Apt 4B",
            city="Santiago",
            region="RM",
            postcode="7500000",
        )

        full_addr = address.full_address

        assert "Main Street" in full_addr
        assert "123" in full_addr
        assert "Unit Apt 4B" in full_addr
        assert "Santiago" in full_addr
        assert "RM" in full_addr
        assert "7500000" in full_addr

    def test_full_address_empty(self):
        """Test full_address cuando no hay campos"""
        address = Address()
        assert address.full_address == ""

    def test_coordinates_property(self):
        """Test propiedad coordinates"""
        address = Address(
            longitude=Decimal("-70.6506"), latitude=Decimal("-33.4372")
        )

        coords = address.coordinates

        assert coords is not None
        assert isinstance(coords, tuple)
        assert len(coords) == 2
        assert coords[0] == -70.6506
        assert coords[1] == -33.4372

    def test_coordinates_property_none(self):
        """Test coordinates cuando no hay coordenadas"""
        address = Address()
        assert address.coordinates is None

        address2 = Address(longitude=Decimal("-70.6506"))
        assert address2.coordinates is None

    def test_repr_method(self):
        """Test método __repr__"""
        address = Address(
            id=1, hash="repr123", street="Test St", number="99", city="Test City"
        )

        repr_str = repr(address)

        assert "Address" in repr_str
        assert "id=1" in repr_str
        assert "hash='repr123'" in repr_str
        assert "Test St" in repr_str or "Test City" in repr_str
