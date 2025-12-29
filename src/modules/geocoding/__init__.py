"""
Colombian Address Geocoding Module

This module provides geocoding services for Colombian addresses,
converting street addresses into geographic coordinates using a
6-phase pipeline:

1. PARSE - Parse address into components
2. SEARCH - Search for matching streets in database
3. MATCH - Find street segment containing target number
4. INTERPOLATE - Calculate position percentage
5. GENERATE - Generate interpolated coordinates
6. OFFSET - Apply lateral offset based on street side

Example usage:
    >>> from src.modules.geocoding import GeocodingService
    >>> from src.database import get_db
    >>>
    >>> async def example():
    ...     async with async_session() as db:
    ...         service = GeocodingService(db)
    ...         result = await service.geocode(
    ...             address="KR 43 # 57 49",
    ...             city="Jardín",
    ...             region="ANT"
    ...         )
    ...         if result.success:
    ...             print(f"Lat: {result.latitude}, Lon: {result.longitude}")
    ...             print(f"Side: {result.side}")
"""

from .service import GeocodingService
from .models import (
    AddressComponents,
    StreetSegment,
    InterpolationResult,
    GeocodingResult,
    AccuracyLevel
)
from .config import GeocodingConfig
from .parser import AddressParser
from .searcher import StreetSearcher
from .interpolator import PositionInterpolator
from .generator import CoordinateGenerator

__all__ = [
    # Main service
    "GeocodingService",

    # Data models
    "AddressComponents",
    "StreetSegment",
    "InterpolationResult",
    "GeocodingResult",
    "AccuracyLevel",

    # Configuration
    "GeocodingConfig",

    # Components (for advanced usage)
    "AddressParser",
    "StreetSearcher",
    "PositionInterpolator",
    "CoordinateGenerator",
]

__version__ = "0.1.0"
