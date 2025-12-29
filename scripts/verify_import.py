"""
Script para verificar los datos importados desde GeoJSON

Muestra estadísticas y ejemplos de los datos en la base de datos
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func, distinct
from src.database.session import async_session
from src.modules.addresses.model import Address


async def verify_import():
    """Verifica y muestra estadísticas de los datos importados"""
    async with async_session() as session:
        print("=" * 80)
        print("VERIFICACIÓN DE DATOS IMPORTADOS")
        print("=" * 80)
        print()

        # Total de registros
        result = await session.execute(select(func.count(Address.id)))
        total = result.scalar()
        print(f"Total de registros: {total:,}")
        print()

        # Registros con coordenadas
        result = await session.execute(
            select(func.count(Address.id)).where(
                Address.longitude.is_not(None), Address.latitude.is_not(None)
            )
        )
        with_coords = result.scalar()
        print(f"Registros con coordenadas: {with_coords:,} ({with_coords/total*100:.1f}%)")

        # Registros únicos por hash
        result = await session.execute(select(func.count(distinct(Address.hash))))
        unique_hashes = result.scalar()
        print(f"Hashes únicos: {unique_hashes:,}")

        # Ciudades únicas
        result = await session.execute(
            select(func.count(distinct(Address.city))).where(Address.city.is_not(None))
        )
        cities = result.scalar()
        print(f"Ciudades únicas: {cities:,}")

        # Regiones únicas
        result = await session.execute(
            select(func.count(distinct(Address.region))).where(
                Address.region.is_not(None)
            )
        )
        regions = result.scalar()
        print(f"Regiones únicas: {regions:,}")
        print()

        # Top 10 ciudades con más direcciones
        print("=" * 80)
        print("TOP 10 CIUDADES CON MÁS DIRECCIONES")
        print("=" * 80)
        result = await session.execute(
            select(Address.city, func.count(Address.id).label("count"))
            .where(Address.city.is_not(None))
            .group_by(Address.city)
            .order_by(func.count(Address.id).desc())
            .limit(10)
        )

        for i, row in enumerate(result.all(), 1):
            print(f"{i:2d}. {row.city:30s} - {row.count:,} direcciones")
        print()

        # Ejemplos de registros
        print("=" * 80)
        print("EJEMPLOS DE REGISTROS (5 primeros)")
        print("=" * 80)
        result = await session.execute(select(Address).limit(5))
        addresses = result.scalars().all()

        for i, addr in enumerate(addresses, 1):
            print(f"\n{i}. ID: {addr.id}")
            print(f"   Hash: {addr.hash}")
            print(f"   Dirección: {addr.full_address}")
            print(f"   Coordenadas: {addr.coordinates}")
            print(f"   External ID: {addr.external_id}")

        print()

        # Verificar Unicode
        print("=" * 80)
        print("VERIFICACIÓN DE UNICODE (caracteres especiales)")
        print("=" * 80)
        result = await session.execute(
            select(Address)
            .where(Address.city.like("%í%") | Address.city.like("%á%"))
            .limit(5)
        )
        unicode_addresses = result.scalars().all()

        if unicode_addresses:
            print("Registros con caracteres especiales encontrados:")
            for addr in unicode_addresses:
                print(f"  - {addr.city}: {addr.street} {addr.number}")
        else:
            print("No se encontraron registros con caracteres especiales en city")
        print()

        # Rangos de coordenadas
        print("=" * 80)
        print("RANGOS DE COORDENADAS")
        print("=" * 80)
        result = await session.execute(
            select(
                func.min(Address.longitude),
                func.max(Address.longitude),
                func.min(Address.latitude),
                func.max(Address.latitude),
            ).where(Address.longitude.is_not(None), Address.latitude.is_not(None))
        )
        min_lng, max_lng, min_lat, max_lat = result.first()

        if min_lng:
            print(f"Longitud: {float(min_lng):.7f} a {float(max_lng):.7f}")
            print(f"Latitud:  {float(min_lat):.7f} a {float(max_lat):.7f}")
        else:
            print("No hay coordenadas disponibles")


if __name__ == "__main__":
    asyncio.run(verify_import())
