"""
Street searcher and segment matcher (Phases 2 & 3)

This module handles database queries to find matching streets and
identify the appropriate street segment for geocoding.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.addresses.model import Address
from .models import StreetSegment, AddressComponents
from .interpolator import PositionInterpolator


class StreetSearcher:
    """
    Searches for streets in the database and matches segments

    Phase 2: Search for streets matching the parsed address
    Phase 3: Find the specific segment containing the target number
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize searcher with database session

        Args:
            db: Async database session
        """
        self.db = db
        self.interpolator = PositionInterpolator()

    async def search_streets(
        self,
        street_name: str,
        city: str,
        region: str = "ANT"
    ) -> List[Address]:
        """
        Search for streets matching the given criteria

        Uses a two-tier search strategy:
        1. Exact match on street name
        2. Fuzzy match with ILIKE if exact match returns no results

        Args:
            street_name: Full street name (e.g., "KR 43")
            city: City name
            region: Region code (default: "ANT")

        Returns:
            List of Address objects ordered by number

        Example:
            >>> searcher = StreetSearcher(db)
            >>> addresses = await searcher.search_streets("KR 43", "Jardín", "ANT")
            >>> len(addresses)  # Number of matching addresses
        """
        # Tier 1: Exact match
        query = select(Address).where(
            Address.city == city,
            Address.street == street_name,
            Address.region == region,
            Address.latitude.isnot(None),
            Address.longitude.isnot(None)
        ).order_by(Address.number).limit(100)

        result = await self.db.execute(query)
        candidates = result.scalars().all()

        if candidates:
            return list(candidates)

        # Tier 2: Fuzzy match with ILIKE
        query = select(Address).where(
            Address.city == city,
            Address.street.ilike(f"%{street_name}%"),
            Address.region == region,
            Address.latitude.isnot(None),
            Address.longitude.isnot(None)
        ).order_by(Address.number).limit(100)

        result = await self.db.execute(query)
        candidates = result.scalars().all()

        return list(candidates)

    async def find_segment(
        self,
        candidates: List[Address],
        target_number: str
    ) -> Optional[StreetSegment]:
        """
        Find street segment containing the target number

        Searches through candidate addresses to find two adjacent addresses
        where the target number falls between their numbers.

        Args:
            candidates: List of Address objects from search
            target_number: Target house/building number (e.g., "57")

        Returns:
            StreetSegment if match found, None otherwise

        Example:
            >>> segment = await searcher.find_segment(candidates, "75")
            >>> if segment:
            ...     print(f"{segment.start_number} - {segment.end_number}")
            ...     # "50 - 100"
        """
        if not candidates:
            return None

        # Parse target number for comparison
        try:
            target_num = self.interpolator.parse_number_simple(target_number)
        except (ValueError, AttributeError):
            return None

        # Sort candidates by number
        sorted_candidates = sorted(
            candidates,
            key=lambda x: self.interpolator.parse_number_simple(x.number) if x.number else 0
        )

        # Try to find exact match first
        for address in sorted_candidates:
            addr_num = self.interpolator.parse_number_simple(address.number)
            if addr_num == target_num:
                # Exact match - create single-point segment
                return StreetSegment(
                    street_name=address.street,
                    start_number=address.number,
                    end_number=address.number,
                    start_lat=address.latitude,
                    start_lon=address.longitude,
                    end_lat=address.latitude,
                    end_lon=address.longitude,
                    city=address.city
                )

        # Find segment containing target number
        for i in range(len(sorted_candidates) - 1):
            curr = sorted_candidates[i]
            next_addr = sorted_candidates[i + 1]

            curr_num = self.interpolator.parse_number_simple(curr.number)
            next_num = self.interpolator.parse_number_simple(next_addr.number)

            # Check if target is between current and next
            if curr_num <= target_num <= next_num:
                return StreetSegment(
                    street_name=curr.street,
                    start_number=curr.number,
                    end_number=next_addr.number,
                    start_lat=curr.latitude,
                    start_lon=curr.longitude,
                    end_lat=next_addr.latitude,
                    end_lon=next_addr.longitude,
                    city=curr.city
                )

        # Fallback: use closest segment
        return self._get_closest_segment(sorted_candidates, target_num)

    def _get_closest_segment(
        self,
        candidates: List[Address],
        target_num: int
    ) -> Optional[StreetSegment]:
        """
        Get segment closest to target number (fallback strategy)

        Args:
            candidates: Sorted list of Address objects
            target_num: Target number as integer

        Returns:
            StreetSegment using the two closest addresses
        """
        if not candidates:
            return None

        if len(candidates) == 1:
            # Only one candidate - create single-point segment
            addr = candidates[0]
            return StreetSegment(
                street_name=addr.street,
                start_number=addr.number,
                end_number=addr.number,
                start_lat=addr.latitude,
                start_lon=addr.longitude,
                end_lat=addr.latitude,
                end_lon=addr.longitude,
                city=addr.city
            )

        # Find closest address
        closest_idx = 0
        min_distance = float('inf')

        for i, address in enumerate(candidates):
            addr_num = self.interpolator.parse_number_simple(address.number)
            distance = abs(addr_num - target_num)
            if distance < min_distance:
                min_distance = distance
                closest_idx = i

        # Create segment using closest and its neighbor
        if closest_idx < len(candidates) - 1:
            # Use closest and next
            curr = candidates[closest_idx]
            next_addr = candidates[closest_idx + 1]
        else:
            # Use previous and closest (for last element)
            curr = candidates[closest_idx - 1]
            next_addr = candidates[closest_idx]

        return StreetSegment(
            street_name=curr.street,
            start_number=curr.number,
            end_number=next_addr.number,
            start_lat=curr.latitude,
            start_lon=curr.longitude,
            end_lat=next_addr.latitude,
            end_lon=next_addr.longitude,
            city=curr.city
        )

    async def get_street_centroid(
        self,
        street_name: str,
        city: str,
        region: str = "ANT"
    ) -> Optional[tuple[float, float]]:
        """
        Calculate centroid of all addresses on a street (fallback)

        Args:
            street_name: Street name
            city: City name
            region: Region code

        Returns:
            Tuple of (latitude, longitude) or None
        """
        candidates = await self.search_streets(street_name, city, region)
        if not candidates:
            return None

        # Calculate average coordinates
        lats = [float(addr.latitude) for addr in candidates if addr.latitude]
        lons = [float(addr.longitude) for addr in candidates if addr.longitude]

        if not lats or not lons:
            return None

        avg_lat = sum(lats) / len(lats)
        avg_lon = sum(lons) / len(lons)

        return (avg_lat, avg_lon)
