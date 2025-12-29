"""
Manejo de sesiones asíncronas de SQLAlchemy
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.database.connection import engine

# Crear sessionmaker asíncrono
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # No expira objetos después de commit
    autoflush=False,         # Control manual de flush
    autocommit=False,        # Transacciones explícitas
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para FastAPI que provee una sesión de base de datos

    Uso:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...

    Yields:
        AsyncSession: Sesión de base de datos asíncrona
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
