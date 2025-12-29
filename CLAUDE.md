# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI-based geolocation API with PostgreSQL database using SQLAlchemy 2.0 async architecture. The project focuses on georeference processing for addresses with geographic coordinates.

## Environment Setup

This project requires a virtual environment. Always ensure the venv is activated before running commands:

**Windows (Git Bash/MINGW64):**
```bash
source venv/Scripts/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Environment variables:**
Copy `.env.example` to `.env` and configure database credentials before running the application.

## Common Commands

### Running the Application
```bash
python main.py
```
Server runs on `http://localhost:8000` with auto-reload in debug mode.

### Database Migrations

**Create migration (autogenerate):**
```bash
alembic revision --autogenerate -m "description"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Revert migration:**
```bash
alembic downgrade -1
```

**Check current migration state:**
```bash
alembic current
```

**View migration history:**
```bash
alembic history
```

### Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_database.py

# Run tests by marker
pytest -m unit
pytest -m integration
pytest -m database
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/
```

## Architecture

### Database Layer (SQLAlchemy 2.0 Async)

The database architecture uses **async/await** throughout with asyncpg driver for PostgreSQL:

**Connection Management (`src/database/connection.py`):**
- `get_database_url()`: Builds PostgreSQL+asyncpg connection string
- `create_engine()`: Creates async engine with different configs for debug vs production
- Debug mode uses `NullPool` (no connection pooling)
- Production uses `AsyncAdaptedQueuePool` with pool_size=5, max_overflow=10, pool_recycle=3600

**Base Models (`src/database/base.py`):**
- `Base`: DeclarativeBase for all models
- `TimestampMixin`: Adds `created_at` and `updated_at` fields with automatic timestamps

**Session Management (`src/database/session.py`):**
- `async_session`: AsyncSession factory
- `get_db()`: Async generator for dependency injection in FastAPI routes

### Alembic Configuration

**Migration naming:** Uses chronological format `YYYY_MM_DD_<revision>_<slug>.py`

**Important implementation detail (`alembic/env.py`):**
- Line 38: All model imports must be added here for autogenerate to detect schema changes
- Lines 84-93: PostgreSQL timeouts are configured (lock_timeout=30s, statement_timeout=60s)
- Uses async migrations with `run_async_migrations()` and `async_engine_from_config()`

### Application Structure

**FastAPI App (`src/app.py`):**
- `create_app()`: Factory function that creates and configures FastAPI instance
- CORS middleware configured to allow all origins (adjust for production)
- Basic routes: `/` (root), `/health` (health check)
- Interactive docs available at `/docs` (Swagger) and `/redoc`

**Configuration (`src/config/settings.py`):**
- Uses `python-dotenv` to load `.env` file
- `Settings` class contains all environment variables
- Global `settings` instance imported throughout the app

**Entry Point (`main.py`):**
- Uses `uvicorn.run()` with `reload=True` in debug mode
- Loads app as string `"src.app:app"` for hot-reload support

## Adding New Models

1. **Create model file** in `src/modules/<module_name>/model.py`
   - Inherit from `Base` and optionally `TimestampMixin`
   - Use SQLAlchemy 2.0 syntax with `Mapped[]` type hints

2. **Import in alembic/env.py** (critical step):
   ```python
   # Add to line ~38-42 area
   from src.modules.<module_name>.model import YourModel  # noqa: F401
   ```

3. **Generate migration:**
   ```bash
   alembic revision --autogenerate -m "add your_model table"
   ```

4. **Review generated migration** before applying (autogenerate can miss some changes)

5. **Apply migration:**
   ```bash
   alembic upgrade head
   ```

## Working with Database Queries

All database operations must use async/await. Key patterns:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db

# In FastAPI routes
async def endpoint(db: AsyncSession = Depends(get_db)):
    # SELECT
    result = await db.execute(select(Model).where(Model.id == 1))
    obj = result.scalar_one_or_none()

    # INSERT
    new_obj = Model(field="value")
    db.add(new_obj)
    await db.commit()
    await db.refresh(new_obj)  # Get auto-generated fields

    # UPDATE
    await db.execute(
        update(Model).where(Model.id == 1).values(field="new_value")
    )
    await db.commit()

    # DELETE
    await db.execute(delete(Model).where(Model.id == 1))
    await db.commit()
```

## Current Models

**Address (`src/modules/addresses/model.py`):**
- Stores address data with geographic coordinates (longitude, latitude)
- Uses `Numeric(10, 7)` for coordinate precision
- Multiple composite indexes for searching by coordinates, city, street, region
- Provides `to_dict()`, `full_address`, and `coordinates` helper methods
- 16-character unique hash field for deduplication

## Testing Setup

**Configuration (`pytest.ini`):**
- Async mode set to `auto`
- Markers defined: `slow`, `integration`, `unit`, `database`
- Test discovery in `tests/` directory

**Fixtures (`conftest.py`):**
- Shared pytest fixtures for database testing

## Key Dependencies

- **FastAPI 0.115.6**: Web framework
- **Uvicorn 0.34.0**: ASGI server
- **SQLAlchemy 2.0.36**: ORM with async support
- **Alembic 1.14.0**: Database migrations
- **asyncpg 0.30.0**: PostgreSQL async driver
- **pytest 8.3.4 + pytest-asyncio 0.25.2**: Testing
- **black 24.10.0**: Code formatter
- **flake8 7.1.1**: Linter

## Important Patterns

**Always use async/await for database operations** - the entire stack is async-based

**Connection pool behavior differs by mode:**
- Debug: No pooling (NullPool) for easier debugging
- Production: Connection pooling with pre-ping and recycling

**Migration imports are critical:**
- If a model isn't imported in `alembic/env.py`, autogenerate won't detect it
- Always verify imports after creating new models

**Commit explicitly:**
- SQLAlchemy 2.0 async requires explicit `await db.commit()`
- Use `db.refresh(obj)` after commit to get server-generated values
