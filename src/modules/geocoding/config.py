"""
Configuration for geocoding service

This module contains configuration settings for the geocoding pipeline.
"""

from dataclasses import dataclass


@dataclass
class GeocodingConfig:
    """
    Configuration parameters for the geocoding service

    Attributes:
        max_search_results: Maximum number of street search results to consider
        default_offset_distance_m: Default lateral offset distance in meters
        fuzzy_search_threshold: Minimum similarity score for fuzzy matching (0-1)
        enable_fallbacks: Whether to use fallback strategies when exact match fails
    """

    # Search parameters
    max_search_results: int = 100
    fuzzy_search_threshold: float = 0.7

    # Interpolation parameters
    default_offset_distance_m: float = 10.0

    # Fallback behavior
    enable_fallbacks: bool = True

    # Accuracy level constants
    ACCURACY_INTERPOLATED = "INTERPOLATED"           # Precise interpolation
    ACCURACY_RANGE_MATCH = "RANGE_MATCH"             # Matched to range
    ACCURACY_STREET_CENTROID = "STREET_CENTROID"     # Street average
    ACCURACY_CITY_CENTROID = "CITY_CENTROID"         # City average
    ACCURACY_PARSE_FAILED = "PARSE_FAILED"           # Parse error
    ACCURACY_NO_STREET_MATCH = "NO_STREET_MATCH"     # Street not found
    ACCURACY_NO_MATCH = "NO_MATCH"                   # No match
    ACCURACY_ERROR = "ERROR"                         # General error
