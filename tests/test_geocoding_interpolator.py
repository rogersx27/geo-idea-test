"""
Unit tests for position interpolator
"""

import pytest
from decimal import Decimal
from src.modules.geocoding.interpolator import PositionInterpolator
from src.modules.geocoding.models import StreetSegment


class TestPositionInterpolator:
    """Test suite for PositionInterpolator"""

    @pytest.fixture
    def interpolator(self):
        """Fixture providing interpolator instance"""
        return PositionInterpolator()

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

    def test_interpolate_at_start(self, interpolator, sample_segment):
        """Test interpolation at segment start (0%)"""
        result = interpolator.interpolate("50", sample_segment)
        assert result.percentage == pytest.approx(0.0)

    def test_interpolate_at_end(self, interpolator, sample_segment):
        """Test interpolation at segment end (100%)"""
        result = interpolator.interpolate("100", sample_segment)
        assert result.percentage == pytest.approx(1.0)

    def test_interpolate_at_midpoint(self, interpolator, sample_segment):
        """Test interpolation at segment midpoint (50%)"""
        result = interpolator.interpolate("75", sample_segment)
        assert result.percentage == pytest.approx(0.5)

    def test_interpolate_at_quarter(self, interpolator, sample_segment):
        """Test interpolation at 25% position"""
        # 50 + (100-50)*0.25 = 62.5 ≈ 62 or 63
        result = interpolator.interpolate("62", sample_segment)
        assert 0.2 < result.percentage < 0.3

    def test_side_determination_odd_is_right(self, interpolator, sample_segment):
        """Test odd number → RIGHT side"""
        result = interpolator.interpolate("75", sample_segment)
        assert result.side == "RIGHT"
        assert result.is_odd == True

    def test_side_determination_even_is_left(self, interpolator, sample_segment):
        """Test even number → LEFT side"""
        result = interpolator.interpolate("74", sample_segment)
        assert result.side == "LEFT"
        assert result.is_odd == False

    def test_parse_number_simple(self, interpolator):
        """Test simple number parsing"""
        assert interpolator._parse_number("57") == 57

    def test_parse_number_with_dash(self, interpolator):
        """Test parsing number with dash separator"""
        assert interpolator._parse_number("57-49") == 5749

    def test_parse_number_with_space(self, interpolator):
        """Test parsing number with space separator"""
        assert interpolator._parse_number("13 247") == 13247

    def test_parse_number_with_letter(self, interpolator):
        """Test parsing number with letter suffix"""
        assert interpolator._parse_number("57A") == 57

    def test_parse_number_empty_string(self, interpolator):
        """Test parsing empty string returns 0"""
        assert interpolator._parse_number("") == 0

    def test_parse_number_simple_static(self):
        """Test static simple parser method"""
        assert PositionInterpolator.parse_number_simple("13 247") == 13
        assert PositionInterpolator.parse_number_simple("57") == 57
        assert PositionInterpolator.parse_number_simple("57A") == 57

    def test_interpolate_beyond_end_clamps_to_one(self, interpolator, sample_segment):
        """Test number beyond end is clamped to 1.0"""
        result = interpolator.interpolate("150", sample_segment)
        assert result.percentage == 1.0

    def test_interpolate_before_start_clamps_to_zero(self, interpolator, sample_segment):
        """Test number before start is clamped to 0.0"""
        result = interpolator.interpolate("25", sample_segment)
        assert result.percentage == 0.0

    def test_interpolate_same_start_end(self, interpolator):
        """Test segment where start equals end"""
        segment = StreetSegment(
            street_name="KR 43",
            start_number="50",
            end_number="50",
            start_lat=Decimal("5.5900"),
            start_lon=Decimal("-75.8200"),
            end_lat=Decimal("5.5900"),
            end_lon=Decimal("-75.8200"),
            city="Jardín"
        )
        result = interpolator.interpolate("50", segment)
        assert result.percentage == 0.0

    def test_interpolate_with_complex_numbers(self, interpolator):
        """Test interpolation with complex number format"""
        segment = StreetSegment(
            street_name="KR 43",
            start_number="57 00",
            end_number="57 99",
            start_lat=Decimal("5.5900"),
            start_lon=Decimal("-75.8200"),
            end_lat=Decimal("5.5950"),
            end_lon=Decimal("-75.8150"),
            city="Jardín"
        )
        result = interpolator.interpolate("57 49", segment)
        # 5749 is roughly halfway between 5700 and 5799
        assert 0.4 < result.percentage < 0.6
