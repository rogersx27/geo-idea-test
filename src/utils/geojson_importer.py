"""
Utilidad para importar direcciones desde archivos GeoJSON
"""
import json
from decimal import Decimal
from typing import Optional, Dict, Any, List, Generator
from pathlib import Path


def parse_geojson_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse una línea de GeoJSON y extrae los datos de dirección

    Args:
        line: Línea de texto con formato GeoJSON

    Returns:
        Dict con los datos mapeados al modelo Address, o None si hay error
    """
    try:
        # Parse JSON - json.loads maneja correctamente Unicode escapado
        data = json.loads(line.strip())

        if data.get("type") != "Feature":
            return None

        properties = data.get("properties", {})
        geometry = data.get("geometry", {})
        coordinates = geometry.get("coordinates", [])

        # Validar que tenemos coordenadas
        if len(coordinates) < 2:
            return None

        # Extraer coordenadas (GeoJSON usa [longitude, latitude])
        longitude = coordinates[0]
        latitude = coordinates[1]

        # Mapear campos al modelo Address
        address_data = {
            "hash": properties.get("hash"),
            "number": properties.get("number") or None,
            "street": properties.get("street") or None,
            "unit": properties.get("unit") or None,
            "city": properties.get("city") or None,
            "district": properties.get("district") or None,
            "region": properties.get("region") or None,
            "postcode": properties.get("postcode") or None,
            "external_id": properties.get("id") or None,  # 'id' -> 'external_id'
            "accuracy": properties.get("accuracy") or None,
            "longitude": Decimal(str(longitude)),
            "latitude": Decimal(str(latitude)),
        }

        # Convertir strings vacías a None
        for key, value in address_data.items():
            if isinstance(value, str) and value.strip() == "":
                address_data[key] = None

        return address_data

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # Retornar None si hay error de parsing
        return None


def count_lines(file_path: Path) -> int:
    """
    Cuenta el número de líneas en un archivo (para mostrar progreso)

    Args:
        file_path: Path al archivo

    Returns:
        Número de líneas
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def read_geojson_batch(
    file_path: Path, batch_size: int = 1000, skip_lines: int = 0
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Lee un archivo GeoJSON línea por línea en lotes

    Args:
        file_path: Path al archivo GeoJSON
        batch_size: Tamaño del lote
        skip_lines: Número de líneas a saltar (para reanudar)

    Yields:
        Lista de dicts con datos de direcciones
    """
    batch = []
    line_count = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_count += 1

            # Saltar líneas si estamos reanudando
            if line_count <= skip_lines:
                continue

            # Parse la línea
            address_data = parse_geojson_line(line)

            if address_data:
                batch.append(address_data)

                # Cuando el lote está lleno, yield y reiniciar
                if len(batch) >= batch_size:
                    yield batch
                    batch = []

        # Yield el último lote si tiene datos
        if batch:
            yield batch
