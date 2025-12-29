"""
Pytest configuration and shared fixtures
"""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy import text

from src.database.connection import engine as db_engine
from src.database.session import async_session
from src.database.base import Base


@pytest.fixture(scope="session")
def engine() -> AsyncEngine:
    """
    Fixture que provee el engine de base de datos para toda la sesión de tests

    Returns:
        AsyncEngine: Motor de base de datos asíncrono
    """
    return db_engine


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture que provee una sesión de base de datos para cada test

    Cada test obtiene una sesión fresca que se hace rollback al finalizar
    para mantener la base de datos limpia.

    Yields:
        AsyncSession: Sesión de base de datos asíncrona
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def db_connection():
    """
    Fixture que provee una conexión directa a la base de datos

    Útil para tests que necesitan ejecutar SQL crudo

    Yields:
        AsyncConnection: Conexión asíncrona a la base de datos
    """
    async with db_engine.connect() as connection:
        try:
            yield connection
        finally:
            await connection.rollback()


@pytest.fixture(scope="session")
def anyio_backend():
    """
    Fixture para configurar el backend de anyio (usado por pytest-asyncio)

    Returns:
        str: Backend a usar (asyncio)
    """
    return "asyncio"
