"""
Colombian address constants and abbreviations

This module contains mappings for Colombian street types, including
abbreviations and long forms commonly used in Colombian addresses.
"""

# Street type mappings (long form → abbreviation)
STREET_TYPE_ABBREVIATIONS = {
    "CALLE": "CL",
    "CARRERA": "KR",
    "AVENIDA": "AV",
    "DIAGONAL": "DG",
    "TRANSVERSAL": "TV",
    "CIRCULAR": "CIR",
    "AUTOPISTA": "AUT",
    "VIA": "VIA",
    # Common variations
    "CR": "KR",  # Normalize CR to KR
    "CA": "CL",  # Calle abbreviated
    "AV": "AV",  # Already abbreviated
    "CL": "CL",  # Already abbreviated
    "KR": "KR",  # Already abbreviated
    "DG": "DG",  # Already abbreviated
    "TV": "TV",  # Already abbreviated
}

# Reverse mapping (abbreviation → long form)
STREET_TYPE_LONG_FORMS = {
    "CL": "CALLE",
    "KR": "CARRERA",
    "AV": "AVENIDA",
    "DG": "DIAGONAL",
    "TV": "TRANSVERSAL",
    "CIR": "CIRCULAR",
    "AUT": "AUTOPISTA",
    "VIA": "VIA",
}

# Common qualifiers used in Colombian addresses
QUALIFIERS = [
    "BIS",     # Bis (in-between)
    "SUR",     # South
    "NORTE",   # North
    "ESTE",    # East
    "OESTE",   # West
    "A", "B", "C", "D", "E",  # Letter qualifiers
]

# Common suffixes
SUFFIXES = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
]
