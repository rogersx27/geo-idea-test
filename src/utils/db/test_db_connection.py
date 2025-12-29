"""
Script para probar la conexión a la base de datos PostgreSQL
"""
import asyncio
from sqlalchemy import text
from src.database.connection import engine


async def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        print("Probando conexión a la base de datos...")
        print(f"URL de conexión: postgresql+asyncpg://{engine.url.username}@{engine.url.host}:{engine.url.port}/{engine.url.database}")

        async with engine.connect() as conn:
            # Ejecutar una consulta simple
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()

            print("\n[OK] Conexion exitosa!")
            print(f"PostgreSQL version: {version}\n")

            # Obtener información adicional
            result = await conn.execute(text("SELECT current_database(), current_user"))
            db_info = result.first()

            print(f"Base de datos: {db_info[0]}")
            print(f"Usuario: {db_info[1]}")

    except Exception as e:
        print(f"\n[ERROR] Error al conectar a la base de datos:")
        print(f"   {str(e)}\n")
        raise
    finally:
        await engine.dispose()
        print("\nConexión cerrada.")


if __name__ == "__main__":
    asyncio.run(test_connection())
