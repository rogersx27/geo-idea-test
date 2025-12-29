"""
Geocoding service orchestrator

This module coordinates all 6 phases of the geocoding pipeline:
1. PARSE - Parse address into components
2. SEARCH - Search for matching streets
3. MATCH - Find street segment containing target number
4. INTERPOLATE - Calculate position percentage
5. GENERATE - Generate interpolated coordinates
6. OFFSET - Apply lateral offset based on street side
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from .models import GeocodingResult, AccuracyLevel
from .config import GeocodingConfig
from .parser import AddressParser
from .searcher import StreetSearcher
from .interpolator import PositionInterpolator
from .generator import CoordinateGenerator


class GeocodingService:
    """
    Main geocoding service orchestrator

    Coordinates the complete geocoding pipeline and provides
    fallback strategies when exact matches are not found.
    """

    def __init__(
        self,
        db: AsyncSession,
        config: Optional[GeocodingConfig] = None
    ):
        """
        Initialize geocoding service

        Args:
            db: Async database session
            config: Optional configuration (uses defaults if not provided)
        """
        self.db = db
        self.config = config or GeocodingConfig()

        # Initialize components
        self.parser = AddressParser()
        self.searcher = StreetSearcher(db)
        self.interpolator = PositionInterpolator()
        self.generator = CoordinateGenerator()

    async def geocode(
        self,
        address: str,
        city: str,
        region: str = "ANT",
        offset_distance: Optional[float] = None
    ) -> GeocodingResult:
        """
        Geocode a Colombian address

        Executes the complete 6-phase pipeline with fallback strategies.

        Args:
            address: Address string (e.g., "KR 43 # 57 49")
            city: City name (e.g., "Jardín")
            region: Region code (default: "ANT")
            offset_distance: Lateral offset in meters (default: from config)

        Returns:
            GeocodingResult with coordinates or error information

        Example:
            >>> service = GeocodingService(db)
            >>> result = await service.geocode("KR 43 # 57 49", "Jardín")
            >>> if result.success:
            ...     print(f"Coordinates: {result.latitude}, {result.longitude}")
            ...     print(f"Side: {result.side}")
            ...     print(f"Accuracy: {result.accuracy}")
        """
        # Use configured offset distance if not provided
        if offset_distance is None:
            offset_distance = self.config.default_offset_distance_m

        try:
            # PHASE 1: PARSE
            components = self.parser.parse(address)
            if not components:
                return GeocodingResult(
                    success=False,
                    latitude=None,
                    longitude=None,
                    accuracy=AccuracyLevel.PARSE_FAILED,
                    side=None,
                    matched_street=None,
                    message=f"Failed to parse address: {address}"
                )

            # PHASE 2: SEARCH
            candidates = await self.searcher.search_streets(
                street_name=components.full_street_name,
                city=city,
                region=region
            )

            if not candidates:
                return GeocodingResult(
                    success=False,
                    latitude=None,
                    longitude=None,
                    accuracy=AccuracyLevel.NO_STREET_MATCH,
                    side=None,
                    matched_street=None,
                    message=f"No streets found matching: {components.full_street_name} in {city}",
                    components=components
                )

            # PHASE 3: MATCH
            segment = await self.searcher.find_segment(
                candidates=candidates,
                target_number=components.number_prefix
            )

            if not segment:
                # Fallback: Use street centroid
                if self.config.enable_fallbacks:
                    centroid = await self.searcher.get_street_centroid(
                        street_name=components.full_street_name,
                        city=city,
                        region=region
                    )
                    if centroid:
                        return GeocodingResult(
                            success=True,
                            latitude=centroid[0],
                            longitude=centroid[1],
                            accuracy=AccuracyLevel.STREET_CENTROID,
                            side=None,
                            matched_street=components.full_street_name,
                            message=f"Used street centroid (number not found in range)",
                            components=components
                        )

                return GeocodingResult(
                    success=False,
                    latitude=None,
                    longitude=None,
                    accuracy=AccuracyLevel.NO_MATCH,
                    side=None,
                    matched_street=None,
                    message=f"Number {components.number_prefix} not found in street range",
                    components=components
                )

            # PHASE 4: INTERPOLATE
            interp_result = self.interpolator.interpolate(
                target_number=components.number_prefix,
                segment=segment
            )

            # PHASE 5: GENERATE
            lat, lon = self.generator.generate_coordinates(
                segment=segment,
                percentage=interp_result.percentage
            )

            # PHASE 6: OFFSET
            final_lat, final_lon = self.generator.apply_lateral_offset(
                lat=lat,
                lon=lon,
                segment=segment,
                side=interp_result.side,
                distance_m=offset_distance
            )

            return GeocodingResult(
                success=True,
                latitude=final_lat,
                longitude=final_lon,
                accuracy=AccuracyLevel.INTERPOLATED,
                side=interp_result.side,
                matched_street=segment.street_name,
                message="Successfully geocoded",
                components=components,
                segment=segment
            )

        except Exception as e:
            return GeocodingResult(
                success=False,
                latitude=None,
                longitude=None,
                accuracy=AccuracyLevel.ERROR,
                side=None,
                matched_street=None,
                message=f"Geocoding error: {str(e)}"
            )

    async def batch_geocode(
        self,
        addresses: list[dict],
        default_region: str = "ANT",
        offset_distance: Optional[float] = None
    ) -> list[GeocodingResult]:
        """
        Geocode multiple addresses in batch

        Args:
            addresses: List of dicts with 'address' and 'city' keys
            default_region: Default region if not specified per address
            offset_distance: Lateral offset in meters

        Returns:
            List of GeocodingResult objects

        Example:
            >>> addresses = [
            ...     {"address": "KR 43 # 57 49", "city": "Jardín"},
            ...     {"address": "CL 100 # 15 20", "city": "Medellín"}
            ... ]
            >>> results = await service.batch_geocode(addresses)
            >>> for result in results:
            ...     if result.success:
            ...         print(f"{result.coordinates}")
        """
        results = []
        for addr_data in addresses:
            result = await self.geocode(
                address=addr_data.get("address"),
                city=addr_data.get("city"),
                region=addr_data.get("region", default_region),
                offset_distance=offset_distance
            )
            results.append(result)
        return results
