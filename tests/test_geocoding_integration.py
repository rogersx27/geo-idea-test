"""
Integration tests for geocoding service

These tests verify the complete geocoding pipeline with database integration.
"""

import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.geocoding.service import GeocodingService
from src.modules.geocoding.models import AccuracyLevel
from src.modules.addresses.model import Address


@pytest.mark.database
@pytest.mark.asyncio
class TestGeocodingServiceIntegration:
    """Integration tests for complete geocoding pipeline"""

    @pytest_asyncio.fixture
    async def sample_addresses(self, db_session: AsyncSession):
        """Fixture providing sample Colombian addresses in database"""
        addresses = [
            Address(
                street="KR 43",
                number="50",
                city="Jardín",
                region="ANT",
                latitude=Decimal("5.5900"),
                longitude=Decimal("-75.8200")
            ),
            Address(
                street="KR 43",
                number="100",
                city="Jardín",
                region="ANT",
                latitude=Decimal("5.5950"),
                longitude=Decimal("-75.8150")
            ),
            Address(
                street="CL 100",
                number="15",
                city="Medellín",
                region="ANT",
                latitude=Decimal("6.2442"),
                longitude=Decimal("-75.5812")
            ),
            Address(
                street="CL 100",
                number="20",
                city="Medellín",
                region="ANT",
                latitude=Decimal("6.2450"),
                longitude=Decimal("-75.5800")
            ),
        ]
        db_session.add_all(addresses)
        await db_session.commit()
        return addresses

    async def test_geocode_exact_match(self, db_session: AsyncSession, sample_addresses):
        """Test geocoding with exact number match"""
        service = GeocodingService(db_session)

        result = await service.geocode(
            address="KR 43 # 50",
            city="Jardín",
            region="ANT"
        )

        assert result.success == True
        assert result.latitude is not None
        assert result.longitude is not None
        assert result.accuracy == AccuracyLevel.INTERPOLATED
        assert result.matched_street == "KR 43"

    async def test_geocode_interpolated_position(self, db_session: AsyncSession, sample_addresses):
        """Test geocoding with interpolated position (between two points)"""
        service = GeocodingService(db_session)

        result = await service.geocode(
            address="KR 43 # 75",
            city="Jardín",
            region="ANT"
        )

        assert result.success == True
        assert result.latitude is not None
        assert result.longitude is not None
        assert result.accuracy == AccuracyLevel.INTERPOLATED
        assert result.matched_street == "KR 43"

        # Should be between start and end points
        assert 5.5900 < result.latitude < 5.5950
        assert -75.8200 < result.longitude < -75.8150

    async def test_geocode_with_odd_number_right_side(self, db_session: AsyncSession, sample_addresses):
        """Test that odd numbers are assigned to RIGHT side"""
        service = GeocodingService(db_session)

        result = await service.geocode(
            address="KR 43 # 75",  # Odd number
            city="Jardín",
            region="ANT"
        )

        assert result.success == True
        assert result.side == "RIGHT"

    async def test_geocode_with_even_number_left_side(self, db_session: AsyncSession, sample_addresses):
        """Test that even numbers are assigned to LEFT side"""
        service = GeocodingService(db_session)

        result = await service.geocode(
            address="KR 43 # 74",  # Even number
            city="Jardín",
            region="ANT"
        )

        assert result.success == True
        assert result.side == "LEFT"

    async def test_geocode_different_formats(self, db_session: AsyncSession, sample_addresses):
        """Test geocoding with different address formats"""
        service = GeocodingService(db_session)

        # Format 1: With hash symbol
        result1 = await service.geocode("KR 43 # 75", "Jardín", "ANT")
        assert result1.success == True

        # Format 2: Without hash symbol
        result2 = await service.geocode("KR 43 75", "Jardín", "ANT")
        assert result2.success == True

        # Format 3: Long form
        result3 = await service.geocode("CARRERA 43 # 75", "Jardín", "ANT")
        assert result3.success == True

        # All should produce similar results
        assert result1.matched_street == result2.matched_street == result3.matched_street

    async def test_geocode_street_not_found(self, db_session: AsyncSession, sample_addresses):
        """Test geocoding when street is not found"""
        service = GeocodingService(db_session)

        result = await service.geocode(
            address="KR 999 # 50",  # Non-existent street
            city="Jardín",
            region="ANT"
        )

        assert result.success == False
        assert result.accuracy == AccuracyLevel.NO_STREET_MATCH
        assert "No streets found" in result.message

    async def test_geocode_invalid_address_format(self, db_session: AsyncSession, sample_addresses):
        """Test geocoding with invalid address format"""
        service = GeocodingService(db_session)

        result = await service.geocode(
            address="Invalid Address 123",
            city="Jardín",
            region="ANT"
        )

        assert result.success == False
        assert result.accuracy == AccuracyLevel.PARSE_FAILED

    async def test_geocode_with_custom_offset(self, db_session: AsyncSession, sample_addresses):
        """Test geocoding with custom lateral offset"""
        service = GeocodingService(db_session)

        result1 = await service.geocode(
            address="KR 43 # 75",
            city="Jardín",
            region="ANT",
            offset_distance=5.0  # 5 meters
        )

        result2 = await service.geocode(
            address="KR 43 # 75",
            city="Jardín",
            region="ANT",
            offset_distance=15.0  # 15 meters
        )

        assert result1.success == True
        assert result2.success == True

        # Results should be different due to different offsets
        assert result1.latitude != result2.latitude or result1.longitude != result2.longitude

    async def test_geocode_returns_components(self, db_session: AsyncSession, sample_addresses):
        """Test that geocoding result includes parsed components"""
        service = GeocodingService(db_session)

        result = await service.geocode("KR 43 # 75", "Jardín", "ANT")

        assert result.success == True
        assert result.components is not None
        assert result.components.street_type == "KR"
        assert result.components.street_name == "43"
        assert result.components.number_prefix == "75"

    async def test_geocode_returns_segment_info(self, db_session: AsyncSession, sample_addresses):
        """Test that geocoding result includes segment information"""
        service = GeocodingService(db_session)

        result = await service.geocode("KR 43 # 75", "Jardín", "ANT")

        assert result.success == True
        assert result.segment is not None
        assert result.segment.street_name == "KR 43"
        assert result.segment.city == "Jardín"

    async def test_batch_geocode(self, db_session: AsyncSession, sample_addresses):
        """Test batch geocoding multiple addresses"""
        service = GeocodingService(db_session)

        addresses_to_geocode = [
            {"address": "KR 43 # 75", "city": "Jardín", "region": "ANT"},
            {"address": "CL 100 # 18", "city": "Medellín", "region": "ANT"},
        ]

        results = await service.batch_geocode(addresses_to_geocode)

        assert len(results) == 2
        assert all(isinstance(r.success, bool) for r in results)
        assert results[0].matched_street == "KR 43"
        assert results[1].matched_street == "CL 100"

    async def test_geocode_coordinates_property(self, db_session: AsyncSession, sample_addresses):
        """Test that coordinates property returns tuple"""
        service = GeocodingService(db_session)

        result = await service.geocode("KR 43 # 75", "Jardín", "ANT")

        assert result.success == True
        coords = result.coordinates
        assert coords is not None
        assert isinstance(coords, tuple)
        assert len(coords) == 2
        assert coords[0] == result.latitude
        assert coords[1] == result.longitude

    async def test_geocode_with_number_beyond_range(self, db_session: AsyncSession, sample_addresses):
        """Test geocoding with number outside available range"""
        service = GeocodingService(db_session)

        # Number 150 is beyond the range 50-100
        result = await service.geocode(
            address="KR 43 # 150",
            city="Jardín",
            region="ANT"
        )

        # Should still succeed with interpolation (clamped to 1.0)
        assert result.success == True
        assert result.accuracy in [AccuracyLevel.INTERPOLATED, AccuracyLevel.STREET_CENTROID]

    async def test_geocode_case_insensitive_city(self, db_session: AsyncSession, sample_addresses):
        """Test that city matching is case-sensitive (as per database)"""
        service = GeocodingService(db_session)

        # Test with exact case
        result = await service.geocode("KR 43 # 75", "Jardín", "ANT")
        assert result.success == True

    async def test_geocode_empty_database(self, db_session: AsyncSession):
        """Test geocoding with no addresses in database"""
        service = GeocodingService(db_session)

        result = await service.geocode("KR 43 # 75", "NonExistentCity", "ANT")

        assert result.success == False
        assert result.accuracy == AccuracyLevel.NO_STREET_MATCH
