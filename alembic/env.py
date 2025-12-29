"""
Alembic environment configuration con soporte para SQLAlchemy 2.0 async
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Importar configuración y modelos de la aplicación
import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from src.database.base import Base
from src.database.connection import get_database_url

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Configurar la URL de la base de datos desde variables de entorno
config.set_main_option("sqlalchemy.url", get_database_url())

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
# Importar todos los modelos aquí para que Alembic los detecte
from src.modules.addresses.model import Address  # noqa: F401

# Otros modelos se importan aquí:
# from src.modules.users.models import User
# from src.modules.products.models import Product

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Ejecuta las migraciones con timeouts configurados para PostgreSQL

    Args:
        connection: Conexión a la base de datos
    """
    # Configurar timeouts de PostgreSQL para evitar bloqueos prolongados
    try:
        connection.execute(
            text("SET lock_timeout = '30s'")
        )  # Timeout para adquirir locks
        connection.execute(
            text("SET statement_timeout = '60s'")
        )  # Timeout para statements individuales
    except Exception as e:
        # Si los timeouts fallan, continuar sin ellos
        print(f"Warning: Could not set timeouts: {e}")

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    In this scenario we need to create an Engine
    and associate a connection with the context.

    This is an async version using asyncpg driver.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,  # SQLAlchemy 2.0 style
    )

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async support."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
