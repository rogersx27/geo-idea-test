"""
Address parser for Colombian addresses (Phase 1)

This module handles parsing of Colombian address formats into structured components.
Supports variations like "KR 43 # 57 49", "Carrera 43 # 57-49", "CL 50 # 60 70", etc.
"""

import re
from typing import Optional
from .models import AddressComponents
from .constants import STREET_TYPE_ABBREVIATIONS


class AddressParser:
    """
    Parser for Colombian address formats

    Handles various format variations:
    - "KR 43 # 57 49"
    - "Carrera 43 # 57-49"
    - "CL 50 # 60 70"
    - "AV 68B # 25 10"
    - "CALLE 100 # 15"
    """

    # Regex pattern for Colombian addresses
    # Captures: street_type, street_name, number_prefix, number_suffix (optional)
    PATTERN = re.compile(
        r'(?P<street_type>AUTOPISTA|TRANSVERSAL|CIRCULAR|DIAGONAL|AVENIDA|CARRERA|CALLE|AUT|CIR|TV|DG|AV|KR|CR|CL|CA)\s*'
        r'(?P<street_name>\d+[A-Z]?)\s*'
        r'#?\s*'
        r'(?P<number_prefix>\d+[A-Z]?)\s*'
        r'[-\s]?\s*'
        r'(?P<number_suffix>\d+)?',
        re.IGNORECASE
    )

    def parse(self, address: str) -> Optional[AddressComponents]:
        """
        Parse a Colombian address string into components

        Args:
            address: Address string to parse (e.g., "KR 43 # 57 49")

        Returns:
            AddressComponents if parsing successful, None otherwise

        Examples:
            >>> parser = AddressParser()
            >>> components = parser.parse("KR 43 # 57 49")
            >>> print(components.street_type)  # "KR"
            >>> print(components.full_street_name)  # "KR 43"
            >>> print(components.full_number)  # "57-49"

            >>> components = parser.parse("CALLE 100 # 15")
            >>> print(components.street_type)  # "CL"
            >>> print(components.number_suffix)  # None
        """
        if not address or not isinstance(address, str):
            return None

        # Search for pattern in address
        match = self.PATTERN.search(address)
        if not match:
            return None

        # Extract components
        street_type_raw = match.group('street_type')
        street_name = match.group('street_name').upper()
        number_prefix = match.group('number_prefix').upper()
        number_suffix = match.group('number_suffix')

        # Normalize street type
        street_type = self._normalize_street_type(street_type_raw)

        # Create AddressComponents
        return AddressComponents(
            street_type=street_type,
            street_name=street_name,
            number_prefix=number_prefix,
            number_suffix=number_suffix.upper() if number_suffix else None,
            raw_address=address
        )

    def _normalize_street_type(self, street_type: str) -> str:
        """
        Normalize street type to standard abbreviation

        Args:
            street_type: Street type to normalize (e.g., "CALLE", "CR", "KR")

        Returns:
            Normalized abbreviation (e.g., "CL", "KR", "AV")

        Examples:
            >>> parser = AddressParser()
            >>> parser._normalize_street_type("CALLE")
            'CL'
            >>> parser._normalize_street_type("CR")
            'KR'
            >>> parser._normalize_street_type("CARRERA")
            'KR'
        """
        street_type_upper = street_type.upper()

        # Check if it's in the abbreviations map
        if street_type_upper in STREET_TYPE_ABBREVIATIONS:
            return STREET_TYPE_ABBREVIATIONS[street_type_upper]

        # If not found, return as-is (uppercase)
        return street_type_upper

    @staticmethod
    def extract_number_value(number_str: str) -> int:
        """
        Extract numeric value from a number string

        Handles formats like "57", "57A", "13 247" (extracts first numeric part)

        Args:
            number_str: Number string to parse

        Returns:
            Integer value of the number

        Examples:
            >>> AddressParser.extract_number_value("57")
            57
            >>> AddressParser.extract_number_value("57A")
            57
            >>> AddressParser.extract_number_value("13 247")
            13
        """
        # Extract first sequence of digits
        match = re.search(r'\d+', str(number_str))
        return int(match.group()) if match else 0
