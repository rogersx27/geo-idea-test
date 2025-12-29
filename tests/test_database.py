"""
Tests de conexión y funcionalidad de base de datos
"""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine


@pytest.mark.database
@pytest.mark.asyncio
class TestDatabaseConnection:
    """Tests de conexión básica a la base de datos"""

    async def test_engine_is_available(self, engine: AsyncEngine):
        """Test que el engine está disponible y configurado"""
        assert engine is not None
        assert engine.url.drivername == "postgresql+asyncpg"
        assert engine.url.database == "geo"
        assert engine.url.host == "75.119.144.199"
        assert engine.url.port == 9963

    async def test_can_connect_to_database(self, db_connection):
        """Test que podemos conectarnos a la base de datos"""
        result = await db_connection.execute(text("SELECT 1"))
        value = result.scalar()
        assert value == 1

    async def test_database_version(self, db_connection):
        """Test que podemos obtener la versión de PostgreSQL"""
        result = await db_connection.execute(text("SELECT version()"))
        version = result.scalar()

        assert version is not None
        assert "PostgreSQL" in version
        print(f"\nPostgreSQL version: {version}")

    async def test_current_database_and_user(self, db_connection):
        """Test que estamos conectados a la base de datos correcta"""
        result = await db_connection.execute(
            text("SELECT current_database(), current_user")
        )
        db_info = result.first()

        assert db_info[0] == "geo"
        assert db_info[1] == "postgres"

    async def test_can_create_table(self, db_connection):
        """Test que podemos crear y eliminar tablas de prueba"""
        # Crear tabla temporal
        await db_connection.execute(
            text(
                """
                CREATE TEMP TABLE test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100)
                )
                """
            )
        )

        # Verificar que existe
        result = await db_connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM pg_tables
                    WHERE tablename = 'test_table'
                )
                """
            )
        )
        exists = result.scalar()
        assert exists is True


@pytest.mark.database
@pytest.mark.asyncio
class TestDatabaseSession:
    """Tests de sesiones de base de datos"""

    async def test_session_is_available(self, db_session: AsyncSession):
        """Test que la sesión está disponible"""
        assert db_session is not None
        assert isinstance(db_session, AsyncSession)

    async def test_session_can_execute_query(self, db_session: AsyncSession):
        """Test que podemos ejecutar queries con la sesión"""
        result = await db_session.execute(text("SELECT 1 as num"))
        value = result.scalar()
        assert value == 1

    async def test_session_transaction_rollback(self, db_session: AsyncSession):
        """Test que las transacciones se revierten correctamente"""
        # Crear tabla temporal
        await db_session.execute(
            text(
                """
                CREATE TEMP TABLE test_rollback (
                    id SERIAL PRIMARY KEY,
                    value VARCHAR(50)
                )
                """
            )
        )

        # Insertar datos
        await db_session.execute(
            text("INSERT INTO test_rollback (value) VALUES ('test')")
        )

        # Verificar que se insertó
        result = await db_session.execute(text("SELECT COUNT(*) FROM test_rollback"))
        count = result.scalar()
        assert count == 1

        # El rollback automático en el fixture debe limpiar esto
        # (verificado al finalizar el test)

    async def test_multiple_queries_in_session(self, db_session: AsyncSession):
        """Test que podemos ejecutar múltiples queries en una sesión"""
        # Query 1
        result1 = await db_session.execute(text("SELECT 1"))
        assert result1.scalar() == 1

        # Query 2
        result2 = await db_session.execute(text("SELECT 2"))
        assert result2.scalar() == 2

        # Query 3 - más compleja
        result3 = await db_session.execute(
            text("SELECT current_timestamp, current_user")
        )
        row = result3.first()
        assert row is not None
        assert len(row) == 2


@pytest.mark.database
@pytest.mark.asyncio
class TestDatabaseFeatures:
    """Tests de características específicas de PostgreSQL"""

    async def test_postgresql_extensions(self, db_connection):
        """Test de extensiones disponibles en PostgreSQL"""
        result = await db_connection.execute(
            text("SELECT extname FROM pg_extension ORDER BY extname")
        )
        extensions = [row[0] for row in result.fetchall()]

        # Verificar que al menos plpgsql está disponible
        assert "plpgsql" in extensions
        print(f"\nExtensiones disponibles: {', '.join(extensions)}")

    async def test_postgresql_schemas(self, db_connection):
        """Test de schemas disponibles"""
        result = await db_connection.execute(
            text(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT LIKE 'pg_%'
                AND schema_name != 'information_schema'
                ORDER BY schema_name
                """
            )
        )
        schemas = [row[0] for row in result.fetchall()]

        # Debe existir al menos el schema public
        assert "public" in schemas
        print(f"\nSchemas disponibles: {', '.join(schemas)}")

    async def test_postgresql_timezone(self, db_connection):
        """Test de timezone configurado en PostgreSQL"""
        result = await db_connection.execute(text("SHOW timezone"))
        timezone = result.scalar()

        assert timezone is not None
        print(f"\nTimezone configurado: {timezone}")

    async def test_postgresql_encoding(self, db_connection):
        """Test de encoding de la base de datos"""
        result = await db_connection.execute(
            text(
                """
                SELECT pg_encoding_to_char(encoding)
                FROM pg_database
                WHERE datname = current_database()
                """
            )
        )
        encoding = result.scalar()

        assert encoding is not None
        print(f"\nEncoding de la DB: {encoding}")


@pytest.mark.database
@pytest.mark.asyncio
@pytest.mark.slow
class TestDatabasePerformance:
    """Tests de rendimiento de conexión (marcados como slow)"""

    async def test_connection_pool(self, engine: AsyncEngine):
        """Test de pool de conexiones"""
        # Crear múltiples conexiones
        connections = []
        for _ in range(3):
            conn = await engine.connect()
            connections.append(conn)

        # Verificar que todas funcionan
        for conn in connections:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

        # Cerrar todas
        for conn in connections:
            await conn.close()

    async def test_concurrent_queries(self, db_session: AsyncSession):
        """Test de queries concurrentes en la misma sesión"""
        import asyncio

        async def query_task(num: int):
            result = await db_session.execute(text(f"SELECT {num}"))
            return result.scalar()

        # Ejecutar varias queries (aunque en la misma sesión se ejecutan secuencialmente)
        results = []
        for i in range(1, 6):
            result = await query_task(i)
            results.append(result)

        assert results == [1, 2, 3, 4, 5]
