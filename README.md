# Georeference Test

Proyecto Python con estructura estándar y buenas prácticas.

## Estructura del Proyecto

```
georeference-test/
├── src/                    # Código fuente
│   ├── config/            # Configuración de la aplicación
│   ├── database/          # Configuración de base de datos (SQLAlchemy 2.0 async)
│   ├── modules/           # Módulos de la aplicación
│   └── utils/             # Utilidades y funciones auxiliares
├── alembic/               # Migraciones de base de datos
│   ├── versions/          # Migraciones (formato cronológico)
│   └── env.py            # Configuración con timeouts
├── tests/                 # Pruebas unitarias y de integración
├── docs/                  # Documentación
├── venv/                  # Entorno virtual (no se versiona)
├── main.py                # Entrypoint de la aplicación
├── alembic.ini            # Configuración de Alembic
├── requirements.txt       # Dependencias del proyecto
├── .env                   # Variables de entorno (no se versiona)
├── .env.example          # Ejemplo de variables de entorno
├── DATABASE_SETUP.md     # Guía de uso de base de datos
└── .gitignore            # Archivos ignorados por Git
```

## Configuración del Entorno

### 1. Activar el entorno virtual

**Windows (Git Bash/MINGW64):**
```bash
source venv/Scripts/activate
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Copiar `.env.example` a `.env` y ajustar los valores según sea necesario:

```bash
cp .env.example .env
```

## Ejecutar el Servidor

```bash
python main.py
```

El servidor estará disponible en `http://localhost:8000`

## Endpoints Disponibles

- `GET /` - Información de la API
- `GET /health` - Health check
- `GET /docs` - Documentación interactiva (Swagger UI)
- `GET /redoc` - Documentación alternativa (ReDoc)

## Desarrollo

### Ejecutar pruebas

```bash
pytest
```

### Formatear código

```bash
black src/ tests/
```

### Linting

```bash
flake8 src/ tests/
```

## Base de Datos

Este proyecto usa **PostgreSQL** con **SQLAlchemy 2.0 async** y **Alembic** para migraciones.

### Comandos de Alembic

```bash
# Crear migración automática
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1

# Ver estado actual
alembic current

# Ver historial
alembic history
```

Ver documentación completa en [DATABASE_SETUP.md](/docs/DATABASE_SETUP.md)

## Stack Tecnológico

- **Framework**: FastAPI 0.115.6
- **Server**: Uvicorn con hot-reload
- **ORM**: SQLAlchemy 2.0 (async con asyncpg)
- **Migraciones**: Alembic 1.14.0
- **Base de datos**: PostgreSQL
- **Testing**: Pytest + pytest-asyncio
- **Code quality**: Black + Flake8

## Notas

- El servidor usa FastAPI y Uvicorn con hot-reload automático
- Las variables de entorno se cargan desde el archivo `.env`
- El modo debug está habilitado por defecto en desarrollo
- Las migraciones usan formato cronológico: `YYYY_MM_DD_<rev>_<slug>.py`
- Los timeouts de PostgreSQL están configurados en `alembic/env.py`
