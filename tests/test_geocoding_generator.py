"""
Unit tests for coordinate generator
"""

import pytest
from decimal import Decimal
from src.modules.geocoding.generator import CoordinateGenerator
from src.modules.geocoding.models import StreetSegment


class TestCoordinateGenerator:
    """Test suite for CoordinateGenerator"""

    @pytest.fixture
    def generator(self):
        """Fixture providing generator instance"""
        return CoordinateGenerator()

    @pytest.fixture
    def sample_segment(self):
        """Fixture providing a sample street segment"""
        return StreetSegment(
            street_name="KR 43",
            start_number="50",
            end_number="100",
            start_lat=Decimal("5.5900"),
            start_lon=Decimal("-75.8200"),
            end_lat=Decimal("5.5950"),
            end_lon=Decimal("-75.8150"),
            city="Jardín"
        )

    def test_generate_coordinates_at_start(self, generator, sample_segment):
        """Test coordinate generation at 0% (start point)"""
        lat, lon = generator.generate_coordinates(sample_segment, 0.0)
        assert lat == pytest.approx(5.5900, abs=1e-6)
        assert lon == pytest.approx(-75.8200, abs=1e-6)

    def test_generate_coordinates_at_end(self, generator, sample_segment):
        """Test coordinate generation at 100% (end point)"""
        lat, lon = generator.generate_coordinates(sample_segment, 1.0)
        assert lat == pytest.approx(5.5950, abs=1e-6)
        assert lon == pytest.approx(-75.8150, abs=1e-6)

    def test_generate_coordinates_at_midpoint(self, generator, sample_segment):
        """Test coordinate generation at 50% (midpoint)"""
        lat, lon = generator.generate_coordinates(sample_segment, 0.5)
        expected_lat = (5.5900 + 5.5950) / 2
        expected_lon = (-75.8200 + -75.8150) / 2
        assert lat == pytest.approx(expected_lat, abs=1e-6)
        assert lon == pytest.approx(expected_lon, abs=1e-6)

    def test_generate_coordinates_at_quarter(self, generator, sample_segment):
        """Test coordinate generation at 25%"""
        lat, lon = generator.generate_coordinates(sample_segment, 0.25)
        expected_lat = 5.5900 + 0.25 * (5.5950 - 5.5900)
        expected_lon = -75.8200 + 0.25 * (-75.8150 - -75.8200)
        assert lat == pytest.approx(expected_lat, abs=1e-6)
        assert lon == pytest.approx(expected_lon, abs=1e-6)

    def test_generate_coordinates_percentage_zero(self, generator, sample_segment):
        """Test with percentage = 0"""
        lat, lon = generator.generate_coordinates(sample_segment, 0.0)
        assert lat == 5.5900
        assert lon == -75.8200

    def test_generate_coordinates_percentage_one(self, generator, sample_segment):
        """Test with percentage = 1"""
        lat, lon = generator.generate_coordinates(sample_segment, 1.0)
        assert lat == 5.5950
        assert lon == -75.8150

    def test_apply_lateral_offset_right_side(self, generator, sample_segment):
        """Test applying offset to RIGHT side"""
        original_lat, original_lon = 5.5925, -75.8175
        new_lat, new_lon = generator.apply_lateral_offset(
            lat=original_lat,
            lon=original_lon,
            segment=sample_segment,
            side="RIGHT",
            distance_m=10.0
        )
        # Coordinates should change
        assert new_lat != original_lat or new_lon != original_lon

    def test_apply_lateral_offset_left_side(self, generator, sample_segment):
        """Test applying offset to LEFT side"""
        original_lat, original_lon = 5.5925, -75.8175
        new_lat, new_lon = generator.apply_lateral_offset(
            lat=original_lat,
            lon=original_lon,
            segment=sample_segment,
            side="LEFT",
            distance_m=10.0
        )
        # Coordinates should change
        assert new_lat != original_lat or new_lon != original_lon

    def test_apply_lateral_offset_zero_distance(self, generator, sample_segment):
        """Test offset with zero distance returns same point"""
        original_lat, original_lon = 5.5925, -75.8175
        new_lat, new_lon = generator.apply_lateral_offset(
            lat=original_lat,
            lon=original_lon,
            segment=sample_segment,
            side="RIGHT",
            distance_m=0.0
        )
        assert new_lat == pytest.approx(original_lat, abs=1e-6)
        assert new_lon == pytest.approx(original_lon, abs=1e-6)

    def test_apply_lateral_offset_symmetric(self, generator, sample_segment):
        """Test that LEFT and RIGHT offsets are symmetric"""
        original_lat, original_lon = 5.5925, -75.8175

        # Offset right
        right_lat, right_lon = generator.apply_lateral_offset(
            lat=original_lat,
            lon=original_lon,
            segment=sample_segment,
            side="RIGHT",
            distance_m=10.0
        )

        # Offset left
        left_lat, left_lon = generator.apply_lateral_offset(
            lat=original_lat,
            lon=original_lon,
            segment=sample_segment,
            side="LEFT",
            distance_m=10.0
        )

        # They should be different from each other
        assert right_lat != left_lat or right_lon != left_lon

    def test_calculate_street_centroid(self, generator, sample_segment):
        """Test calculating street centroid (midpoint)"""
        lat, lon = generator.calculate_street_centroid(sample_segment)
        expected_lat = (5.5900 + 5.5950) / 2
        expected_lon = (-75.8200 + -75.8150) / 2
        assert lat == pytest.approx(expected_lat, abs=1e-6)
        assert lon == pytest.approx(expected_lon, abs=1e-6)

    def test_generate_coordinates_linear_interpolation(self, generator, sample_segment):
        """Test that interpolation is linear"""
        # Get coordinates at 25%, 50%, 75%
        lat_25, lon_25 = generator.generate_coordinates(sample_segment, 0.25)
        lat_50, lon_50 = generator.generate_coordinates(sample_segment, 0.50)
        lat_75, lon_75 = generator.generate_coordinates(sample_segment, 0.75)

        # Verify linear relationship
        # lat_50 should be average of lat_25 and lat_75
        assert lat_50 == pytest.approx((lat_25 + lat_75) / 2, abs=1e-6)
        assert lon_50 == pytest.approx((lon_25 + lon_75) / 2, abs=1e-6)
