"""
Unit tests for Colombian address parser
"""

import pytest
from src.modules.geocoding.parser import AddressParser


class TestAddressParser:
    """Test suite for AddressParser"""

    @pytest.fixture
    def parser(self):
        """Fixture providing parser instance"""
        return AddressParser()

    def test_parse_standard_format_with_hash(self, parser):
        """Test parsing 'KR 43 # 57 49'"""
        result = parser.parse("KR 43 # 57 49")
        assert result is not None
        assert result.street_type == "KR"
        assert result.street_name == "43"
        assert result.number_prefix == "57"
        assert result.number_suffix == "49"
        assert result.full_street_name == "KR 43"
        assert result.full_number == "57-49"

    def test_parse_without_hash_symbol(self, parser):
        """Test parsing 'CL 100 15 20'"""
        result = parser.parse("CL 100 15 20")
        assert result is not None
        assert result.street_type == "CL"
        assert result.street_name == "100"
        assert result.number_prefix == "15"
        assert result.number_suffix == "20"

    def test_parse_with_dash_separator(self, parser):
        """Test parsing 'Carrera 43 # 57-49'"""
        result = parser.parse("Carrera 43 # 57-49")
        assert result is not None
        assert result.street_type == "KR"  # Normalized from CARRERA
        assert result.street_name == "43"
        assert result.number_prefix == "57"
        assert result.number_suffix == "49"

    def test_parse_with_letter_in_street_name(self, parser):
        """Test parsing 'AV 68B # 25 10'"""
        result = parser.parse("AV 68B # 25 10")
        assert result is not None
        assert result.street_type == "AV"
        assert result.street_name == "68B"
        assert result.number_prefix == "25"
        assert result.number_suffix == "10"

    def test_parse_without_suffix(self, parser):
        """Test parsing address without number suffix"""
        result = parser.parse("CALLE 100 # 15")
        assert result is not None
        assert result.street_type == "CL"  # Normalized from CALLE
        assert result.street_name == "100"
        assert result.number_prefix == "15"
        assert result.number_suffix is None
        assert result.full_number == "15"

    def test_normalize_street_type_calle(self, parser):
        """Test normalization: CALLE → CL"""
        result = parser.parse("CALLE 100 # 15 20")
        assert result.street_type == "CL"

    def test_normalize_street_type_carrera(self, parser):
        """Test normalization: CARRERA → KR"""
        result = parser.parse("CARRERA 43 # 57 49")
        assert result.street_type == "KR"

    def test_normalize_street_type_cr_to_kr(self, parser):
        """Test normalization: CR → KR"""
        result = parser.parse("CR 43 # 57 49")
        assert result.street_type == "KR"

    def test_normalize_street_type_avenida(self, parser):
        """Test normalization: AVENIDA → AV"""
        result = parser.parse("AVENIDA 80 # 45 30")
        assert result.street_type == "AV"

    def test_parse_diagonal(self, parser):
        """Test parsing diagonal"""
        result = parser.parse("DIAGONAL 45 # 20 15")
        assert result is not None
        assert result.street_type == "DG"

    def test_parse_transversal(self, parser):
        """Test parsing transversal"""
        result = parser.parse("TRANSVERSAL 33 # 12 40")
        assert result is not None
        assert result.street_type == "TV"

    def test_parse_case_insensitive(self, parser):
        """Test that parsing is case-insensitive"""
        result = parser.parse("kr 43 # 57 49")
        assert result is not None
        assert result.street_type == "KR"
        assert result.street_name == "43"

    def test_parse_invalid_address_returns_none(self, parser):
        """Test that invalid address returns None"""
        result = parser.parse("Invalid Address 123")
        assert result is None

    def test_parse_empty_string_returns_none(self, parser):
        """Test that empty string returns None"""
        result = parser.parse("")
        assert result is None

    def test_parse_none_returns_none(self, parser):
        """Test that None input returns None"""
        result = parser.parse(None)
        assert result is None

    def test_extract_number_value_simple(self, parser):
        """Test extracting number from simple string"""
        value = parser.extract_number_value("57")
        assert value == 57

    def test_extract_number_value_with_letter(self, parser):
        """Test extracting number from string with letter"""
        value = parser.extract_number_value("57A")
        assert value == 57

    def test_extract_number_value_with_space(self, parser):
        """Test extracting number from string with space"""
        value = parser.extract_number_value("13 247")
        assert value == 13

    def test_raw_address_preserved(self, parser):
        """Test that original address is preserved"""
        original = "KR 43 # 57 49"
        result = parser.parse(original)
        assert result.raw_address == original

    def test_parse_with_extra_whitespace(self, parser):
        """Test parsing with extra whitespace"""
        result = parser.parse("KR  43   #   57   49")
        assert result is not None
        assert result.street_type == "KR"
        assert result.street_name == "43"
        assert result.number_prefix == "57"
        assert result.number_suffix == "49"
