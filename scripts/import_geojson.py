"""
Script para importar direcciones desde archivo GeoJSON a la base de datos

Uso:
    python scripts/import_geojson.py source.geojson
    python scripts/import_geojson.py source.geojson --batch-size 5000
    python scripts/import_geojson.py source.geojson --skip 10000  # Reanudar
"""
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert

from src.database.session import async_session
from src.modules.addresses.model import Address
from src.utils.geojson_importer import read_geojson_batch, count_lines


class ImportStats:
    """Clase para llevar estadísticas de la importación"""

    def __init__(self):
        self.total_lines = 0
        self.processed = 0
        self.inserted = 0
        self.updated = 0
        self.skipped = 0
        self.errors = 0
        self.start_time = datetime.now()

    def elapsed_time(self) -> str:
        """Retorna el tiempo transcurrido"""
        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def progress_percent(self) -> float:
        """Retorna el porcentaje de progreso"""
        if self.total_lines == 0:
            return 0.0
        return (self.processed / self.total_lines) * 100

    def eta(self) -> str:
        """Estima el tiempo restante"""
        if self.processed == 0:
            return "Calculando..."

        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.processed / elapsed  # registros por segundo
        remaining = self.total_lines - self.processed

        if rate > 0:
            eta_seconds = remaining / rate
            hours, remainder = divmod(int(eta_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "Desconocido"

    def print_progress(self):
        """Imprime el progreso actual"""
        print(
            f"\rProcesadas: {self.processed:,}/{self.total_lines:,} "
            f"({self.progress_percent():.1f}%) | "
            f"Insertadas: {self.inserted:,} | "
            f"Actualizadas: {self.updated:,} | "
            f"Errores: {self.errors:,} | "
            f"Tiempo: {self.elapsed_time()} | "
            f"ETA: {self.eta()}",
            end="",
            flush=True,
        )


async def bulk_upsert_addresses(
    batch: List[Dict[str, Any]], stats: ImportStats
) -> None:
    """
    Inserta o actualiza un lote de direcciones usando UPSERT de PostgreSQL

    Args:
        batch: Lista de dicts con datos de direcciones
        stats: Objeto de estadísticas
    """
    async with async_session() as session:
        try:
            # Preparar statement de INSERT con ON CONFLICT
            stmt = insert(Address).values(batch)

            # ON CONFLICT DO UPDATE - actualiza si el hash ya existe
            stmt = stmt.on_conflict_do_update(
                index_elements=["hash"],
                set_={
                    "number": stmt.excluded.number,
                    "street": stmt.excluded.street,
                    "unit": stmt.excluded.unit,
                    "city": stmt.excluded.city,
                    "district": stmt.excluded.district,
                    "region": stmt.excluded.region,
                    "postcode": stmt.excluded.postcode,
                    "external_id": stmt.excluded.external_id,
                    "accuracy": stmt.excluded.accuracy,
                    "longitude": stmt.excluded.longitude,
                    "latitude": stmt.excluded.latitude,
                },
            )

            # Ejecutar
            await session.execute(stmt)
            await session.commit()

            # Contar como insertadas (simplificado, no diferenciamos insert vs update)
            stats.inserted += len(batch)

        except Exception as e:
            await session.rollback()
            stats.errors += len(batch)
            print(f"\n[ERROR] Batch error: {str(e)[:100]}")


async def import_geojson(
    file_path: Path,
    batch_size: int = 1000,
    skip_lines: int = 0,
    count_total: bool = True,
) -> ImportStats:
    """
    Importa direcciones desde un archivo GeoJSON

    Args:
        file_path: Path al archivo GeoJSON
        batch_size: Tamaño de lotes para bulk insert
        skip_lines: Líneas a saltar (para reanudar)
        count_total: Si contar el total de líneas primero (puede ser lento)

    Returns:
        ImportStats con las estadísticas de la importación
    """
    stats = ImportStats()

    # Contar total de líneas (opcional, puede ser lento en archivos grandes)
    if count_total:
        print("Contando total de líneas...")
        stats.total_lines = count_lines(file_path)
        print(f"Total de líneas: {stats.total_lines:,}\n")
    else:
        stats.total_lines = skip_lines + 1000000  # Estimación

    # Procesar el archivo por lotes
    print(f"Iniciando importación (batch_size={batch_size})...")
    print(f"Archivo: {file_path}")
    if skip_lines > 0:
        print(f"Reanudando desde línea {skip_lines:,}")
    print()

    batch_count = 0
    for batch in read_geojson_batch(file_path, batch_size, skip_lines):
        batch_count += 1
        stats.processed += len(batch)

        # Insertar el lote
        await bulk_upsert_addresses(batch, stats)

        # Mostrar progreso
        stats.print_progress()

        # Guardar checkpoint cada 10 lotes
        if batch_count % 10 == 0:
            checkpoint_file = Path("import_checkpoint.txt")
            checkpoint_file.write_text(str(stats.processed + skip_lines))

    # Línea final
    print("\n\nImportación completada!")
    return stats


async def get_current_count() -> int:
    """Obtiene el conteo actual de registros en la tabla"""
    async with async_session() as session:
        result = await session.execute(select(func.count(Address.id)))
        return result.scalar()


async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Importar direcciones desde archivo GeoJSON"
    )
    parser.add_argument("file", type=str, help="Path al archivo GeoJSON")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Tamaño de lotes para bulk insert (default: 1000)",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Número de líneas a saltar (para reanudar)",
    )
    parser.add_argument(
        "--no-count",
        action="store_true",
        help="No contar total de líneas (más rápido en archivos grandes)",
    )

    args = parser.parse_args()

    # Verificar que el archivo existe
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: El archivo {file_path} no existe")
        sys.exit(1)

    # Mostrar conteo actual
    print("=" * 80)
    print("IMPORTACIÓN DE GEOJSON A BASE DE DATOS")
    print("=" * 80)
    current_count = await get_current_count()
    print(f"Registros actuales en la base de datos: {current_count:,}\n")

    # Buscar checkpoint si existe
    checkpoint_file = Path("import_checkpoint.txt")
    if checkpoint_file.exists() and args.skip == 0:
        checkpoint_lines = int(checkpoint_file.read_text().strip())
        print(f"Se encontró checkpoint en línea {checkpoint_lines:,}")
        resume = input("¿Desea reanudar desde ahí? (s/n): ")
        if resume.lower() == "s":
            args.skip = checkpoint_lines

    # Ejecutar importación
    try:
        stats = await import_geojson(
            file_path, args.batch_size, args.skip, not args.no_count
        )

        # Mostrar estadísticas finales
        print("\n" + "=" * 80)
        print("ESTADÍSTICAS FINALES")
        print("=" * 80)
        print(f"Líneas procesadas:   {stats.processed:,}")
        print(f"Registros insertados: {stats.inserted:,}")
        print(f"Registros actualizados: {stats.updated:,}")
        print(f"Errores:             {stats.errors:,}")
        print(f"Tiempo total:        {stats.elapsed_time()}")
        print()

        # Mostrar conteo final
        final_count = await get_current_count()
        print(f"Registros totales en BD: {final_count:,}")
        print(f"Incremento:           {final_count - current_count:,}")

        # Limpiar checkpoint si terminó exitosamente
        if checkpoint_file.exists():
            checkpoint_file.unlink()

    except KeyboardInterrupt:
        print("\n\n[!] Importación interrumpida por el usuario")
        print(f"Puede reanudar usando: --skip {stats.processed}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Error fatal: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
