# Georeference Test

Proyecto Python con estructura estándar y buenas prácticas.

## Estructura del Proyecto

```
georeference-test/
├── src/                    # Código fuente
│   ├── config/            # Configuración de la aplicación
│   ├── modules/           # Módulos de la aplicación
│   └── utils/             # Utilidades y funciones auxiliares
├── tests/                 # Pruebas unitarias y de integración
├── docs/                  # Documentación
├── venv/                  # Entorno virtual (no se versiona)
├── main.py                # Entrypoint de la aplicación
├── requirements.txt       # Dependencias del proyecto
├── .env                   # Variables de entorno (no se versiona)
├── .env.example          # Ejemplo de variables de entorno
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

## Notas

- El servidor usa FastAPI y Uvicorn
- Las variables de entorno se cargan desde el archivo `.env`
- El modo debug está habilitado por defecto en desarrollo
