# Scripts de Importación y Utilidades

Este directorio contiene scripts para importar y gestionar datos de direcciones.

## Filtrar GeoJSON por Ciudad o Región

Antes de importar, puedes filtrar el archivo para incluir solo ciertas ciudades o regiones.

### Uso Rápido - Medellín/Antioquia

```bash
# Windows
scripts\extract_medellin.bat

# Linux/Mac
bash scripts/extract_medellin.sh
```

Esto crea dos archivos:
- `medellin.geojson` - Solo direcciones de Medellín
- `antioquia.geojson` - Todas las direcciones de la región ANT

### Uso Avanzado - Filtrar Manualmente

```bash
# Solo Medellín
python scripts/filter_geojson.py source.geojson --city "Medellín" -o medellin.geojson

# Solo región ANT (Antioquia)
python scripts/filter_geojson.py source.geojson --region "ANT" -o antioquia.geojson

# Múltiples ciudades
python scripts/filter_geojson.py source.geojson \
    --city "Medellín" --city "Bogotá" --city "Cali" \
    -o principales.geojson

# Múltiples regiones
python scripts/filter_geojson.py source.geojson \
    --region "ANT" --region "CUN" --region "VAC" \
    -o regiones.geojson

# Combinación (Medellín Y que esté en ANT)
python scripts/filter_geojson.py source.geojson \
    --city "Medellín" --region "ANT" \
    --match-mode all \
    -o medellin_ant.geojson
```

**Opciones:**
- `-c, --city`: Ciudad a filtrar (puede repetirse)
- `-r, --region`: Región a filtrar (puede repetirse)
- `-o, --output`: Archivo de salida (requerido)
- `-m, --match-mode`: `any` (OR) o `all` (AND), default: `any`

## Importar GeoJSON

### Uso Básico

```bash
# Importar archivo completo
python scripts/import_geojson.py source.geojson

# Con tamaño de lote personalizado (mejor rendimiento)
python scripts/import_geojson.py source.geojson --batch-size 5000

# Sin contar líneas totales (más rápido para archivos grandes)
python scripts/import_geojson.py source.geojson --no-count
```

### Reanudar Importación Interrumpida

Si la importación se interrumpe, puedes reanudarla desde donde quedó:

```bash
# El script guarda checkpoints automáticamente
# Al ejecutar nuevamente, preguntará si deseas reanudar
python scripts/import_geojson.py source.geojson

# O especificar manualmente desde qué línea reanudar
python scripts/import_geojson.py source.geojson --skip 50000
```

### Características

**Rendimiento:**
- Lectura streaming (no carga todo en memoria)
- Bulk insert con UPSERT de PostgreSQL
- Procesamiento por lotes configurable
- Checkpoints automáticos cada 10 lotes

**Manejo de Datos:**
- Unicode correcto (e.g., `\u00ed` → `í`)
- UPSERT: actualiza si el hash ya existe
- Validación de coordenadas
- Strings vacías convertidas a NULL

**Progreso:**
- Barra de progreso en tiempo real
- Estimación de tiempo restante (ETA)
- Contador de errores
- Estadísticas al finalizar

### Formato del Archivo GeoJSON

El script espera un archivo con formato NDJSON (una Feature por línea):

```json
{"type": "Feature", "properties": {"hash": "abc123", "number": "123", "street": "Main St", "city": "Santiago", "region": "RM", "id": "ext001"}, "geometry": {"type": "Point", "coordinates": [-70.6506, -33.4372]}}
```

**Mapeo de campos:**
- `properties.hash` → `hash`
- `properties.number` → `number`
- `properties.street` → `street`
- `properties.unit` → `unit`
- `properties.city` → `city`
- `properties.district` → `district`
- `properties.region` → `region`
- `properties.postcode` → `postcode`
- `properties.id` → `external_id`
- `properties.accuracy` → `accuracy`
- `geometry.coordinates[0]` → `longitude`
- `geometry.coordinates[1]` → `latitude`

## Verificar Importación

Después de importar, verifica los datos:

```bash
python scripts/verify_import.py
```

**Muestra:**
- Total de registros
- Registros con coordenadas
- Ciudades y regiones únicas
- Top 10 ciudades
- Ejemplos de registros
- Verificación de Unicode
- Rangos de coordenadas

## Limpiar Base de Datos

Para eliminar todos los registros importados:

```bash
python clean_test_data.py
```

## Ejemplos de Uso

### Importación Rápida (archivo pequeño)

```bash
python scripts/import_geojson.py data.geojson --batch-size 10000
```

### Importación de Archivo Grande (2GB+)

```bash
# Primera ejecución - no contar líneas para empezar más rápido
python scripts/import_geojson.py source.geojson --batch-size 5000 --no-count

# Si se interrumpe, el script guarda checkpoint automáticamente
# Al volver a ejecutar, pregunta si quieres reanudar
python scripts/import_geojson.py source.geojson --batch-size 5000
```

### Verificar Progreso Durante Importación

El script muestra progreso en tiempo real:

```
Procesadas: 50,000/1,234,567 (4.0%) | Insertadas: 49,950 | Actualizadas: 0 | Errores: 50 | Tiempo: 00:02:30 | ETA: 01:00:15
```

### Después de Importar

```bash
# Verificar los datos
python scripts/verify_import.py

# Iniciar el servidor para usar la API
python main.py
```

## Solución de Problemas

### Error de memoria

Si encuentras errores de memoria, reduce el batch size:

```bash
python scripts/import_geojson.py source.geojson --batch-size 500
```

### Errores de duplicados

El script usa UPSERT basado en el campo `hash`. Si un hash ya existe, actualiza el registro en lugar de insertar uno nuevo.

### Caracteres Unicode

El script maneja automáticamente caracteres especiales:
- `Legu\u00edzamo` → `Leguízamo`
- `Bogot\u00e1` → `Bogotá`

### Checkpoint no funciona

Si el checkpoint no se guarda correctamente, puedes especificar manualmente:

```bash
# Ver cuántos registros hay actualmente
python scripts/verify_import.py

# Reanudar desde esa cantidad
python scripts/import_geojson.py source.geojson --skip 50000
```

## Rendimiento Esperado

En una máquina promedio con conexión remota a PostgreSQL:

- **Velocidad**: ~1,000-5,000 registros/segundo
- **Archivo de 2GB**: ~1-2 horas (depende de red y hardware)
- **Memoria**: <500MB (lectura streaming)

**Optimizaciones:**
- Usar `--batch-size 5000` o mayor
- Usar `--no-count` para archivos muy grandes
- Ejecutar cerca de la base de datos (misma red)
- Desactivar índices temporalmente si importas millones de registros
