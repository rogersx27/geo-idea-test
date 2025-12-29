"""
Internal data models for geocoding pipeline

This module defines dataclasses used for internal data flow between
the different phases of the geocoding pipeline.
"""

from dataclasses import dataclass
from typing import Optional, Literal
from decimal import Decimal


@dataclass
class AddressComponents:
    """
    Parsed components of a Colombian address

    Example:
        "KR 43 # 57 49" →
        AddressComponents(
            street_type="KR",
            street_name="43",
            number_prefix="57",
            number_suffix="49",
            raw_address="KR 43 # 57 49"
        )
    """
    street_type: str                      # CL, KR, AV, etc.
    street_name: str                      # "43", "43A", etc.
    number_prefix: str                    # "57"
    number_suffix: Optional[str] = None   # "49" or None
    raw_address: str = ""                 # Original input

    @property
    def full_street_name(self) -> str:
        """Returns complete street name (e.g., 'KR 43')"""
        return f"{self.street_type} {self.street_name}"

    @property
    def full_number(self) -> str:
        """Returns complete number (e.g., '57-49' or '57')"""
        if self.number_suffix:
            return f"{self.number_prefix}-{self.number_suffix}"
        return self.number_prefix


@dataclass
class StreetSegment:
    """
    Street segment with two endpoints for interpolation

    Represents a segment of a street between two known addresses,
    used for coordinate interpolation.
    """
    street_name: str                     # "KR 43"
    start_number: str                    # "50"
    end_number: str                      # "100"
    start_lat: Decimal                   # Starting latitude
    start_lon: Decimal                   # Starting longitude
    end_lat: Decimal                     # Ending latitude
    end_lon: Decimal                     # Ending longitude
    city: str                            # "Jardín"

    @property
    def start_coordinates(self) -> tuple[float, float]:
        """Returns (lat, lon) for start point"""
        return (float(self.start_lat), float(self.start_lon))

    @property
    def end_coordinates(self) -> tuple[float, float]:
        """Returns (lat, lon) for end point"""
        return (float(self.end_lat), float(self.end_lon))


@dataclass
class InterpolationResult:
    """
    Result of position interpolation within a street segment

    Contains the percentage position along the segment and
    the determined side of the street.
    """
    percentage: float                           # 0.0 to 1.0
    side: Literal["LEFT", "RIGHT"]              # Side of street
    is_odd: bool                                # Whether number is odd

    def __post_init__(self):
        """Validate percentage is in valid range"""
        if not 0.0 <= self.percentage <= 1.0:
            raise ValueError(f"Percentage must be between 0 and 1, got {self.percentage}")


@dataclass
class GeocodingResult:
    """
    Final result of the geocoding process

    This is the complete output of the geocoding pipeline, including
    coordinates, accuracy level, and metadata about the process.
    """
    success: bool                                # Whether geocoding succeeded
    latitude: Optional[float]                    # Final latitude
    longitude: Optional[float]                   # Final longitude
    accuracy: str                                # INTERPOLATED, RANGE_MATCH, etc.
    side: Optional[Literal["LEFT", "RIGHT"]]     # Side of street
    matched_street: Optional[str]                # Matched street name
    message: str                                 # Human-readable message
    components: Optional[AddressComponents] = None    # Parsed components
    segment: Optional[StreetSegment] = None          # Matched segment

    @property
    def coordinates(self) -> Optional[tuple[float, float]]:
        """Returns (lat, lon) tuple if geocoding succeeded"""
        if self.success and self.latitude is not None and self.longitude is not None:
            return (self.latitude, self.longitude)
        return None


# Accuracy level constants
class AccuracyLevel:
    """Constants for geocoding accuracy levels"""
    INTERPOLATED = "INTERPOLATED"           # Precise interpolation between two points
    RANGE_MATCH = "RANGE_MATCH"             # Matched to a street segment
    STREET_CENTROID = "STREET_CENTROID"     # Centroid of entire street
    CITY_CENTROID = "CITY_CENTROID"         # Centroid of city
    PARSE_FAILED = "PARSE_FAILED"           # Could not parse address
    NO_STREET_MATCH = "NO_STREET_MATCH"     # Street not found in database
    NO_MATCH = "NO_MATCH"                   # No match found
    ERROR = "ERROR"                         # Error occurred during geocoding
