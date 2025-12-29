# Configuración de Base de Datos - SQLAlchemy 2.0 + Alembic

Este proyecto usa **SQLAlchemy 2.0** con soporte asíncrono y **Alembic** para migraciones de base de datos.

## Stack Tecnológico

- **Base de datos**: PostgreSQL
- **ORM**: SQLAlchemy 2.0 (async con asyncpg)
- **Migraciones**: Alembic
- **Driver**: asyncpg

## Estructura de Carpetas

```
src/database/
├── __init__.py           # Exporta Base, get_db, async_session
├── connection.py         # Configuración del engine y conexión
├── base.py              # Base declarativa y mixins
└── session.py           # Manejo de sesiones asíncronas

alembic/
├── versions/            # Migraciones (con nombres cronológicos)
├── env.py              # Configuración de Alembic con timeouts
└── script.py.mako      # Template para nuevas migraciones

alembic.ini             # Configuración de Alembic
```

## Configuración de Conexión

Las credenciales están en `.env`:

```bash
DB_HOST=75.999.999.999
DB_PORT=6969
DB_NAME=geo
DB_USER=postgres
DB_PASSWORD=********
```

## Características Implementadas

### 1. SQLAlchemy 2.0 Async

- **Engine asíncrono** con asyncpg
- **Pool de conexiones** configurado (size=5, max_overflow=10)
- **Pool pre-ping** para verificar conexiones
- **Pool recycle** cada hora
- **NullPool en debug** para desarrollo

### 2. Alembic con Migraciones Cronológicas

Template de archivos: `YYYY_MM_DD_<revision>_<slug>.py`

Ejemplo: `2025_12_28_a1b2c3d4_create_users_table.py`

### 3. Timeouts de PostgreSQL

Configurados en `alembic/env.py` para evitar bloqueos:

- **lock_timeout**: 30 segundos
- **statement_timeout**: 60 segundos

### 4. Base Declarativa y Mixins

**TimestampMixin**: Agrega campos automáticos `created_at` y `updated_at`

```python
from src.database.base import Base, TimestampMixin

class MyModel(Base, TimestampMixin):
    __tablename__ = "my_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
```

## Uso de Alembic

### Verificar conexión

```bash
alembic current
```

### Crear una nueva migración

**Automática (recomendado)**:
```bash
alembic revision --autogenerate -m "create users table"
```

**Manual**:
```bash
alembic revision -m "add custom index"
```

### Aplicar migraciones

**Última versión**:
```bash
alembic upgrade head
```

**Versión específica**:
```bash
alembic upgrade <revision>
```

### Revertir migraciones

**Una versión atrás**:
```bash
alembic downgrade -1
```

**A versión específica**:
```bash
alembic downgrade <revision>
```

**Revertir todo**:
```bash
alembic downgrade base
```

### Ver historial

```bash
alembic history --verbose
```

### Ver SQL sin aplicar

```bash
alembic upgrade head --sql
```

## Crear un Nuevo Modelo

### 1. Crear el archivo del modelo

```python
# src/modules/users/models.py
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.database.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
```

### 2. Importar el modelo en alembic/env.py

```python
# alembic/env.py (línea ~37)
from src.modules.users.models import User
```

### 3. Generar y aplicar migración

```bash
alembic revision --autogenerate -m "add users table"
alembic upgrade head
```

## Uso en FastAPI

### Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

### Consultas con SQLAlchemy 2.0

```python
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

# SELECT
async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

# INSERT
async def create_user(db: AsyncSession, email: str, username: str):
    user = User(email=email, username=username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# UPDATE
async def update_user(db: AsyncSession, user_id: int, username: str):
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(username=username)
    )
    await db.commit()

# DELETE
async def delete_user(db: AsyncSession, user_id: int):
    await db.execute(
        delete(User).where(User.id == user_id)
    )
    await db.commit()
```

## Mejores Prácticas

1. **Siempre usa `await`** con operaciones de base de datos
2. **Importa todos los modelos** en `alembic/env.py` para autogenerate
3. **Revisa las migraciones** generadas automáticamente antes de aplicarlas
4. **Usa transacciones explícitas** cuando sea necesario
5. **No olvides `await db.commit()`** después de modificaciones
6. **Usa `db.refresh(obj)`** después de commit para obtener valores generados

## Troubleshooting

### Error: "Target database is not up to date"
```bash
alembic stamp head
```

### Error: "Can't locate revision identified by..."
```bash
alembic history
alembic stamp <última_revision>
```

### Ver estado actual
```bash
alembic current
alembic history
```

### Rollback de emergencia
```bash
alembic downgrade -1
```

## Recursos

- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/current/)
