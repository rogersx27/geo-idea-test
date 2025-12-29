"""
Geographic utility functions for geocoding

This module provides mathematical functions for geographic calculations including:
- Haversine distance calculation
- Bearing (azimuth) calculation
- Coordinate offset calculation
"""

import math
from typing import Tuple


# Earth radius in meters
EARTH_RADIUS_METERS = 6371000


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points using Haversine formula

    Args:
        lat1: Latitude of first point (degrees)
        lon1: Longitude of first point (degrees)
        lat2: Latitude of second point (degrees)
        lon2: Longitude of second point (degrees)

    Returns:
        Distance in meters

    Example:
        >>> distance = haversine_distance(5.5900, -75.8200, 5.5950, -75.8150)
        >>> print(f"{distance:.2f} meters")
    """
    # Convert degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_METERS * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate initial bearing (azimuth) from point 1 to point 2

    The bearing is the direction angle measured clockwise from north (0°).

    Args:
        lat1: Latitude of starting point (degrees)
        lon1: Longitude of starting point (degrees)
        lat2: Latitude of destination point (degrees)
        lon2: Longitude of destination point (degrees)

    Returns:
        Bearing in degrees (0-360)

    Example:
        >>> bearing = calculate_bearing(5.5900, -75.8200, 5.5950, -75.8150)
        >>> print(f"Bearing: {bearing:.2f}°")
    """
    # Convert to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    # Calculate bearing
    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    initial_bearing = math.atan2(x, y)

    # Convert to degrees and normalize to 0-360
    bearing = (math.degrees(initial_bearing) + 360) % 360

    return bearing


def offset_coordinate(
    lat: float,
    lon: float,
    bearing: float,
    distance_m: float
) -> Tuple[float, float]:
    """
    Calculate new coordinate at a given distance and bearing from origin

    This function computes a destination point given a starting point,
    a bearing (direction), and a distance.

    Args:
        lat: Origin latitude (degrees)
        lon: Origin longitude (degrees)
        bearing: Bearing/direction in degrees (0-360, where 0 is north)
        distance_m: Distance to offset in meters

    Returns:
        Tuple of (new_latitude, new_longitude) in degrees

    Example:
        >>> # Offset 10 meters to the east (bearing 90°)
        >>> new_lat, new_lon = offset_coordinate(5.5900, -75.8200, 90, 10)
        >>> print(f"New position: {new_lat}, {new_lon}")
    """
    # Angular distance in radians
    d = distance_m / EARTH_RADIUS_METERS

    # Convert to radians
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    brng = math.radians(bearing)

    # Calculate new latitude
    lat2 = math.asin(
        math.sin(lat1) * math.cos(d)
        + math.cos(lat1) * math.sin(d) * math.cos(brng)
    )

    # Calculate new longitude
    lon2 = lon1 + math.atan2(
        math.sin(brng) * math.sin(d) * math.cos(lat1),
        math.cos(d) - math.sin(lat1) * math.sin(lat2)
    )

    # Convert back to degrees
    return (math.degrees(lat2), math.degrees(lon2))


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamp a value between minimum and maximum bounds

    Args:
        value: Value to clamp
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Clamped value

    Example:
        >>> clamp(1.5, 0.0, 1.0)
        1.0
        >>> clamp(-0.5, 0.0, 1.0)
        0.0
        >>> clamp(0.5, 0.0, 1.0)
        0.5
    """
    return max(min_value, min(max_value, value))
