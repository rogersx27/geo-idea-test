"""
Coordinate generator and offset calculator (Phases 5 & 6)

This module generates interpolated coordinates along a street segment
and applies lateral offsets to position points on the correct side of the street.
"""

from typing import Tuple, Literal
from .models import StreetSegment
from .utils import calculate_bearing, offset_coordinate


class CoordinateGenerator:
    """
    Generates coordinates via interpolation and lateral offset

    Phase 5: Linear interpolation between segment endpoints
    Phase 6: Apply perpendicular offset based on street side
    """

    def generate_coordinates(
        self,
        segment: StreetSegment,
        percentage: float
    ) -> Tuple[float, float]:
        """
        Generate coordinates by linear interpolation along a segment

        Args:
            segment: Street segment with start and end coordinates
            percentage: Position along segment (0.0 = start, 1.0 = end)

        Returns:
            Tuple of (latitude, longitude)

        Example:
            >>> generator = CoordinateGenerator()
            >>> segment = StreetSegment(
            ...     street_name="KR 43",
            ...     start_number="50", end_number="100",
            ...     start_lat=Decimal("5.5900"), start_lon=Decimal("-75.8200"),
            ...     end_lat=Decimal("5.5950"), end_lon=Decimal("-75.8150"),
            ...     city="Jardín"
            ... )
            >>> lat, lon = generator.generate_coordinates(segment, 0.5)
            >>> # Returns midpoint: (5.5925, -75.8175)
        """
        # Get start and end coordinates
        start_lat = float(segment.start_lat)
        start_lon = float(segment.start_lon)
        end_lat = float(segment.end_lat)
        end_lon = float(segment.end_lon)

        # Linear interpolation
        lat = start_lat + percentage * (end_lat - start_lat)
        lon = start_lon + percentage * (end_lon - start_lon)

        return (lat, lon)

    def apply_lateral_offset(
        self,
        lat: float,
        lon: float,
        segment: StreetSegment,
        side: Literal["LEFT", "RIGHT"],
        distance_m: float = 10.0
    ) -> Tuple[float, float]:
        """
        Apply perpendicular offset from street centerline

        Calculates a new position offset perpendicular to the street
        direction, placing the point on the correct side of the street.

        Args:
            lat: Original latitude
            lon: Original longitude
            segment: Street segment (used to calculate street bearing)
            side: Side of street ("LEFT" or "RIGHT")
            distance_m: Offset distance in meters (default: 10.0)

        Returns:
            Tuple of (new_latitude, new_longitude)

        Example:
            >>> generator = CoordinateGenerator()
            >>> # Offset 10 meters to the right of the street
            >>> new_lat, new_lon = generator.apply_lateral_offset(
            ...     lat=5.5925,
            ...     lon=-75.8175,
            ...     segment=segment,
            ...     side="RIGHT",
            ...     distance_m=10.0
            ... )
        """
        # Calculate street bearing (direction)
        bearing = calculate_bearing(
            float(segment.start_lat),
            float(segment.start_lon),
            float(segment.end_lat),
            float(segment.end_lon)
        )

        # Calculate perpendicular offset bearing
        # RIGHT = +90° from street direction
        # LEFT = -90° from street direction
        if side == "RIGHT":
            offset_bearing = bearing + 90
        else:  # LEFT
            offset_bearing = bearing - 90

        # Normalize bearing to 0-360 range
        offset_bearing = offset_bearing % 360

        # Calculate new coordinates with offset
        new_lat, new_lon = offset_coordinate(
            lat, lon, offset_bearing, distance_m
        )

        return (new_lat, new_lon)

    def calculate_street_centroid(
        self,
        segment: StreetSegment
    ) -> Tuple[float, float]:
        """
        Calculate centroid (center point) of a street segment

        This is used as a fallback when precise interpolation is not possible.

        Args:
            segment: Street segment

        Returns:
            Tuple of (latitude, longitude) at the center of the segment

        Example:
            >>> generator = CoordinateGenerator()
            >>> centroid = generator.calculate_street_centroid(segment)
            >>> # Returns center point between start and end
        """
        return self.generate_coordinates(segment, 0.5)
