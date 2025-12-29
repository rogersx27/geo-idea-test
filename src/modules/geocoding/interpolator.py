"""
Position interpolator for address geocoding (Phase 4)

This module calculates the position percentage of a target address number
within a street segment and determines the side of the street (LEFT/RIGHT).
"""

import re
from .models import StreetSegment, InterpolationResult
from .utils import clamp


class PositionInterpolator:
    """
    Calculates position within a street segment

    Determines:
    1. Percentage position along the segment (0.0 to 1.0)
    2. Side of the street (LEFT/RIGHT) based on odd/even number
    """

    def interpolate(
        self,
        target_number: str,
        segment: StreetSegment
    ) -> InterpolationResult:
        """
        Calculate position percentage and street side for target number

        Args:
            target_number: Target address number (e.g., "57", "57-49")
            segment: Street segment with start and end numbers

        Returns:
            InterpolationResult with percentage and side

        Example:
            >>> interpolator = PositionInterpolator()
            >>> segment = StreetSegment(
            ...     street_name="KR 43",
            ...     start_number="50",
            ...     end_number="100",
            ...     start_lat=Decimal("5.5900"), start_lon=Decimal("-75.8200"),
            ...     end_lat=Decimal("5.5950"), end_lon=Decimal("-75.8150"),
            ...     city="Jardín"
            ... )
            >>> result = interpolator.interpolate("75", segment)
            >>> print(result.percentage)  # 0.5
            >>> print(result.side)  # "RIGHT" (75 is odd)
        """
        # Parse numbers to integers
        target_num = self._parse_number(target_number)
        start_num = self._parse_number(segment.start_number)
        end_num = self._parse_number(segment.end_number)

        # Calculate percentage
        if end_num == start_num:
            # If start and end are the same, place at the start
            percentage = 0.0
        else:
            percentage = (target_num - start_num) / (end_num - start_num)

        # Clamp to [0, 1]
        percentage = clamp(percentage, 0.0, 1.0)

        # Determine side (Colombian convention: odd = RIGHT, even = LEFT)
        is_odd = target_num % 2 == 1
        side = "RIGHT" if is_odd else "LEFT"

        return InterpolationResult(
            percentage=percentage,
            side=side,
            is_odd=is_odd
        )

    def _parse_number(self, number_str: str) -> int:
        """
        Parse address number to integer for comparison

        Handles formats:
        - "57" → 57
        - "57-49" → 5749
        - "13 247" → 13247 (extracts all digits)
        - "57A" → 57

        Args:
            number_str: Number string to parse

        Returns:
            Integer representation

        Examples:
            >>> interpolator = PositionInterpolator()
            >>> interpolator._parse_number("57")
            57
            >>> interpolator._parse_number("57-49")
            5749
            >>> interpolator._parse_number("13 247")
            13247
        """
        if not number_str:
            return 0

        # Remove all non-digit characters and concatenate digits
        digits = re.findall(r'\d+', str(number_str))
        if not digits:
            return 0

        # For Colombian addresses, concatenate all digit groups
        # "57-49" → "5749", "13 247" → "13247"
        full_number = ''.join(digits)
        return int(full_number)

    @staticmethod
    def parse_number_simple(number_str: str) -> int:
        """
        Simple number parser that extracts only the first numeric portion

        This is useful for database queries where the number field
        might have the format "13 247" and we only want "13"

        Args:
            number_str: Number string (e.g., "13 247", "57", "57A")

        Returns:
            First numeric portion as integer

        Examples:
            >>> PositionInterpolator.parse_number_simple("13 247")
            13
            >>> PositionInterpolator.parse_number_simple("57")
            57
            >>> PositionInterpolator.parse_number_simple("57A")
            57
        """
        match = re.search(r'\d+', str(number_str))
        return int(match.group()) if match else 0
