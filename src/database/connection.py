"""
Configuración de conexión a la base de datos con SQLAlchemy 2.0
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from src.config.settings import settings

def get_database_url() -> str:
    """
    Construye la URL de conexión para PostgreSQL con asyncpg

    Returns:
        str: URL de conexión asíncrona
    """
    return (
        f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )

def create_engine() -> AsyncEngine:
    """
    Crea el motor asíncrono de SQLAlchemy con configuración optimizada

    Returns:
        AsyncEngine: Motor de base de datos asíncrono
    """
    # Configuración base del engine
    engine_config = {
        "url": get_database_url(),
        "echo": settings.DEBUG,
        "future": True,
    }

    # Agregar configuración de pool según el modo
    if settings.DEBUG:
        # En modo debug, usar NullPool (sin pool de conexiones)
        engine_config["poolclass"] = NullPool
    else:
        # En producción, usar pool de conexiones optimizado
        engine_config.update({
            "poolclass": AsyncAdaptedQueuePool,
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        })

    engine = create_async_engine(**engine_config)
    return engine

# Instancia global del engine
engine = create_engine()
