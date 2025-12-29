"""
Unit tests for geographic utility functions
"""

import pytest
import math
from src.modules.geocoding.utils import (
    haversine_distance,
    calculate_bearing,
    offset_coordinate,
    clamp
)


class TestHaversineDistance:
    """Test suite for Haversine distance calculation"""

    def test_distance_same_point(self):
        """Test distance from a point to itself is zero"""
        distance = haversine_distance(5.5900, -75.8200, 5.5900, -75.8200)
        assert distance == pytest.approx(0, abs=1)

    def test_distance_known_coordinates(self):
        """Test distance between two known points"""
        # Approximately 700 meters apart
        distance = haversine_distance(5.5900, -75.8200, 5.5950, -75.8150)
        assert 600 < distance < 800  # Rough range check

    def test_distance_is_symmetric(self):
        """Test that distance(A, B) == distance(B, A)"""
        dist1 = haversine_distance(5.5900, -75.8200, 5.5950, -75.8150)
        dist2 = haversine_distance(5.5950, -75.8150, 5.5900, -75.8200)
        assert dist1 == pytest.approx(dist2, rel=1e-9)

    def test_distance_positive(self):
        """Test that distance is always positive"""
        distance = haversine_distance(0, 0, 1, 1)
        assert distance > 0


class TestCalculateBearing:
    """Test suite for bearing calculation"""

    def test_bearing_north(self):
        """Test bearing directly north is 0°"""
        bearing = calculate_bearing(0, 0, 1, 0)
        assert bearing == pytest.approx(0, abs=1)

    def test_bearing_east(self):
        """Test bearing directly east is 90°"""
        bearing = calculate_bearing(0, 0, 0, 1)
        assert bearing == pytest.approx(90, abs=1)

    def test_bearing_south(self):
        """Test bearing directly south is 180°"""
        bearing = calculate_bearing(1, 0, 0, 0)
        assert bearing == pytest.approx(180, abs=1)

    def test_bearing_west(self):
        """Test bearing directly west is 270°"""
        bearing = calculate_bearing(0, 1, 0, 0)
        assert bearing == pytest.approx(270, abs=1)

    def test_bearing_range(self):
        """Test bearing is always in range 0-360"""
        bearing = calculate_bearing(5.5900, -75.8200, 5.5950, -75.8150)
        assert 0 <= bearing < 360

    def test_bearing_same_point(self):
        """Test bearing from point to itself"""
        # Should be 0 or 360, but behavior may vary
        bearing = calculate_bearing(5.5900, -75.8200, 5.5900, -75.8200)
        assert 0 <= bearing < 360


class TestOffsetCoordinate:
    """Test suite for coordinate offset calculation"""

    def test_offset_north(self):
        """Test offsetting north increases latitude"""
        lat, lon = offset_coordinate(0, 0, 0, 1000)  # 1km north
        assert lat > 0
        assert lon == pytest.approx(0, abs=1e-6)

    def test_offset_east(self):
        """Test offsetting east increases longitude"""
        lat, lon = offset_coordinate(0, 0, 90, 1000)  # 1km east
        assert lat == pytest.approx(0, abs=1e-6)
        assert lon > 0

    def test_offset_south(self):
        """Test offsetting south decreases latitude"""
        lat, lon = offset_coordinate(0, 0, 180, 1000)  # 1km south
        assert lat < 0
        assert lon == pytest.approx(0, abs=1e-6)

    def test_offset_west(self):
        """Test offsetting west decreases longitude"""
        lat, lon = offset_coordinate(0, 0, 270, 1000)  # 1km west
        assert lat == pytest.approx(0, abs=1e-6)
        assert lon < 0

    def test_offset_zero_distance(self):
        """Test zero offset returns same point"""
        lat, lon = offset_coordinate(5.5900, -75.8200, 0, 0)
        assert lat == pytest.approx(5.5900, rel=1e-9)
        assert lon == pytest.approx(-75.8200, rel=1e-9)

    def test_offset_small_distance(self):
        """Test small offset (10 meters)"""
        original_lat, original_lon = 5.5900, -75.8200
        new_lat, new_lon = offset_coordinate(original_lat, original_lon, 90, 10)

        # Verify it moved
        distance = haversine_distance(original_lat, original_lon, new_lat, new_lon)
        assert distance == pytest.approx(10, rel=0.1)  # Within 10% tolerance

    def test_offset_roundtrip(self):
        """Test offset and reverse offset returns to origin"""
        original_lat, original_lon = 5.5900, -75.8200

        # Offset 100m east
        lat1, lon1 = offset_coordinate(original_lat, original_lon, 90, 100)

        # Offset 100m west (back)
        lat2, lon2 = offset_coordinate(lat1, lon1, 270, 100)

        assert lat2 == pytest.approx(original_lat, abs=1e-6)
        assert lon2 == pytest.approx(original_lon, abs=1e-6)


class TestClamp:
    """Test suite for clamp utility function"""

    def test_clamp_value_below_min(self):
        """Test clamping value below minimum"""
        result = clamp(-0.5, 0.0, 1.0)
        assert result == 0.0

    def test_clamp_value_above_max(self):
        """Test clamping value above maximum"""
        result = clamp(1.5, 0.0, 1.0)
        assert result == 1.0

    def test_clamp_value_in_range(self):
        """Test value within range is unchanged"""
        result = clamp(0.5, 0.0, 1.0)
        assert result == 0.5

    def test_clamp_value_at_min(self):
        """Test value at minimum boundary"""
        result = clamp(0.0, 0.0, 1.0)
        assert result == 0.0

    def test_clamp_value_at_max(self):
        """Test value at maximum boundary"""
        result = clamp(1.0, 0.0, 1.0)
        assert result == 1.0

    def test_clamp_negative_range(self):
        """Test clamping in negative range"""
        result = clamp(-5.0, -10.0, -1.0)
        assert result == -5.0

    def test_clamp_large_positive_range(self):
        """Test clamping in large positive range"""
        result = clamp(500, 0, 1000)
        assert result == 500
