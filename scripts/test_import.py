"""
Script de prueba para verificar que el importador funciona correctamente

Crea un archivo GeoJSON de prueba y lo importa
"""
import sys
import asyncio
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.geojson_importer import parse_geojson_line
from src.database.session import async_session
from src.modules.addresses.model import Address
from sqlalchemy import select


# Datos de prueba (copiados de tu ejemplo)
SAMPLE_DATA = [
    {
        "type": "Feature",
        "properties": {
            "hash": "68d6f7ab4dbddee4",
            "number": "0 0",
            "street": "KR 1",
            "unit": "",
            "city": "Puerto Leguízamo",  # Con Unicode normal
            "district": "",
            "region": "PUT",
            "postcode": "",
            "id": "6rfyf7dcg",
            "accuracy": "",
        },
        "geometry": {"type": "Point", "coordinates": [-74.7800088, -0.2001786]},
    },
    {
        "type": "Feature",
        "properties": {
            "hash": "ccf4925f51821cc5",
            "number": "1 1",
            "street": "KR 1",
            "unit": "",
            "city": "Puerto Legu\u00edzamo",  # Con Unicode escapado
            "district": "",
            "region": "PUT",
            "postcode": "",
            "id": "6rfyf7du3",
            "accuracy": "",
        },
        "geometry": {"type": "Point", "coordinates": [-74.7800946, -0.1997495]},
    },
    {
        "type": "Feature",
        "properties": {
            "hash": "306651d06d7e034a",
            "number": "2 35",
            "street": "KR 1",
            "unit": "",
            "city": "Puerto Leguízamo",
            "district": "",
            "region": "PUT",
            "postcode": "",
            "id": "6rfyf7dx5",
            "accuracy": "",
        },
        "geometry": {"type": "Point", "coordinates": [-74.7803521, -0.1992774]},
    },
]


def test_parse_geojson():
    """Prueba el parser de GeoJSON"""
    print("=" * 80)
    print("TEST 1: Parse de líneas GeoJSON")
    print("=" * 80)

    for i, data in enumerate(SAMPLE_DATA, 1):
        line = json.dumps(data, ensure_ascii=False)
        parsed = parse_geojson_line(line)

        print(f"\nLínea {i}:")
        print(f"  Input city: {data['properties']['city']}")
        print(f"  Parsed city: {parsed['city']}")
        print(f"  Hash: {parsed['hash']}")
        print(f"  Coordenadas: ({parsed['longitude']}, {parsed['latitude']})")

        # Verificar que el Unicode se maneja correctamente
        assert parsed["city"] == "Puerto Leguízamo", "Unicode no se procesó correctamente"
        assert parsed["hash"] is not None
        assert parsed["longitude"] is not None
        assert parsed["latitude"] is not None

    print("\n✓ Todos los tests de parsing pasaron")


async def test_insert():
    """Prueba insertar los datos en la base de datos"""
    print("\n" + "=" * 80)
    print("TEST 2: Inserción en la base de datos")
    print("=" * 80)

    async with async_session() as session:
        # Limpiar datos de prueba anteriores
        await session.execute(
            select(Address).where(Address.hash.in_(
                ["68d6f7ab4dbddee4", "ccf4925f51821cc5", "306651d06d7e034a"]
            ))
        )
        result = await session.execute(
            select(Address).where(Address.hash == "68d6f7ab4dbddee4")
        )
        existing = result.scalar_one_or_none()
        if existing:
            await session.delete(existing)
            await session.commit()
            print("Datos de prueba anteriores eliminados")

        # Insertar datos de prueba
        for data in SAMPLE_DATA:
            line = json.dumps(data, ensure_ascii=False)
            parsed = parse_geojson_line(line)

            address = Address(**parsed)
            session.add(address)

        await session.commit()
        print(f"✓ {len(SAMPLE_DATA)} registros insertados")

        # Verificar que se insertaron correctamente
        result = await session.execute(
            select(Address).where(Address.city == "Puerto Leguízamo")
        )
        addresses = result.scalars().all()

        print(f"\nRegistros encontrados: {len(addresses)}")
        for addr in addresses:
            print(f"  - {addr.street} {addr.number}, {addr.city}")
            print(f"    Hash: {addr.hash}")
            print(f"    Coordenadas: {addr.coordinates}")

        assert len(addresses) >= 3, "No se encontraron todos los registros"
        print("\n✓ Verificación exitosa")


async def test_unicode():
    """Prueba específica de manejo de Unicode"""
    print("\n" + "=" * 80)
    print("TEST 3: Manejo de Unicode")
    print("=" * 80)

    # Test con diferentes formas de Unicode
    test_cases = [
        ("Puerto Leguízamo", "Unicode normal"),
        ("Puerto Legu\u00edzamo", "Unicode escapado"),
        ("Bogotá D.C.", "Unicode normal con acento"),
        ("Bogot\u00e1 D.C.", "Unicode escapado con acento"),
    ]

    for city, description in test_cases:
        feature = {
            "type": "Feature",
            "properties": {
                "hash": f"test_{hash(city)}",
                "city": city,
                "street": "Test St",
                "id": "test123",
            },
            "geometry": {"type": "Point", "coordinates": [-74.0, -4.0]},
        }

        line = json.dumps(feature, ensure_ascii=False)
        parsed = parse_geojson_line(line)

        print(f"\n{description}:")
        print(f"  Input:  {city}")
        print(f"  Output: {parsed['city']}")

        # Verificar que no hay caracteres escapados en el resultado
        assert "\\u" not in parsed["city"], f"Unicode no procesado en: {parsed['city']}"

    print("\n✓ Todos los tests de Unicode pasaron")


async def main():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 80)
    print("TESTS DEL IMPORTADOR GEOJSON")
    print("=" * 80)
    print()

    try:
        # Test 1: Parsing
        test_parse_geojson()

        # Test 2: Inserción
        await test_insert()

        # Test 3: Unicode
        await test_unicode()

        print("\n" + "=" * 80)
        print("✓ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 80)
        print("\nEl importador está listo para usar con archivos grandes.")
        print("Ejecuta: python scripts/import_geojson.py source.geojson")

    except AssertionError as e:
        print(f"\n✗ TEST FALLÓ: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
