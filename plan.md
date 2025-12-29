Plan de Implementación: Sistema de Geocodificación para Direcciones Colombianas

 Resumen Ejecutivo

 Implementar un sistema de geocodificación en 6 fases que convierta direcciones colombianas (ej: "KR 43 # 57 49") en coordenadas geográficas precisas mediante interpolación sobre datos existentes en la tabla
 addresses.

 Arquitectura Propuesta

 src/modules/geocoding/
 ├── __init__.py              # Exporta GeocodingService y schemas públicos
 ├── service.py               # GeocodingService - Orquestador principal (6 fases)
 ├── models.py                # Dataclasses internos (AddressComponents, StreetSegment, etc.)
 ├── schemas.py               # Pydantic models para API (opcional)
 ├── config.py                # GeocodingConfig - Configuración
 ├── parser.py                # Fase 1: Parseo de direcciones colombianas
 ├── searcher.py              # Fase 2-3: Búsqueda y matching de segmentos
 ├── interpolator.py          # Fase 4: Cálculo de posición relativa
 ├── generator.py             # Fase 5-6: Generación de coordenadas + offset
 ├── utils.py                 # Haversine, bearing, offset_coordinate
 ├── constants.py             # Diccionario de abreviaturas colombianas
 └── router.py (opcional)     # Endpoints FastAPI

 Integración con Codebase Existente

 Modelo Address Existente

 - Ubicación: src/modules/addresses/model.py
 - Campos clave: street (String 200), number (String 50), city, region, latitude (Numeric 10,7), longitude (Numeric 10,7)
 - Índices disponibles:
   - idx_addresses_full (city, street, number)
   - idx_addresses_coords (longitude, latitude)
   - idx_addresses_street, idx_addresses_city, idx_addresses_region

 Patrón de Sesiones Async

 from sqlalchemy.ext.asyncio import AsyncSession
 from src.database import get_db

 # Dependency injection en FastAPI
 async def endpoint(db: AsyncSession = Depends(get_db)):
     service = GeocodingService(db)
     result = await service.geocode(...)

 Pipeline de Geocodificación (6 Fases)

 Fase 1: PARSE - Parseo de Dirección

 Archivo: parser.py

 Responsabilidad: Convertir texto en componentes estructurados

 Input: "KR 43 # 57 49" o "Carrera 43 # 57-49" o "CL 50 # 60 70"

 Output:
 AddressComponents(
     street_type="KR",      # Normalizado
     street_name="43",
     number_prefix="57",
     number_suffix="49",
     raw_address="KR 43 # 57 49"
 )

 Implementación:
 - Regex pattern: (KR|CR|CL|AV|CALLE|CARRERA)\s*(\d+[A-Z]?)\s*#?\s*(\d+[A-Z]?)\s*(\d+)?
 - Normalizar abreviaturas: CALLE → CL, CARRERA → KR, CR → KR
 - Manejar variaciones: con/sin #, con/sin guión, con/sin espacios
 - Retornar None si no parseable

 Fase 2: SEARCH - Búsqueda de Calle

 Archivo: searcher.py

 Responsabilidad: Buscar calles coincidentes en tabla addresses

 Estrategia de búsqueda:
 1. Tier 1 - Exacta:
 SELECT * FROM addresses
 WHERE city = ? AND street = ? AND region = ?
 ORDER BY number
 1. Usa índice idx_addresses_full
 2. Tier 2 - Fuzzy (si Tier 1 vacío):
 SELECT * FROM addresses
 WHERE city = ? AND street ILIKE '%{street_name}%' AND region = ?
 ORDER BY number
 LIMIT 100

 Output: Lista de Address objetos ordenados por número

 Fase 3: MATCH - Encontrar Segmento

 Archivo: searcher.py (método find_segment)

 Responsabilidad: Identificar segmento que contiene el número objetivo

 Algoritmo:
 1. Parsear números de direcciones (ej: "13 247" → 13)
 2. Ordenar por número
 3. Buscar par adyacente donde: start_num <= target <= end_num
 4. Si coincidencia exacta, usar esa dirección
 5. Si no hay match, usar segmento más cercano (fallback)

 Output:
 StreetSegment(
     street_name="KR 43",
     start_number="50",
     end_number="100",
     start_lat=Decimal("5.5900"),
     start_lon=Decimal("-75.8200"),
     end_lat=Decimal("5.5950"),
     end_lon=Decimal("-75.8150"),
     city="Jardín"
 )

 Fase 4: INTERPOLATE - Calcular Posición

 Archivo: interpolator.py

 Responsabilidad: Calcular % de posición y lado de calle

 Algoritmo:
 target = parse_number("57")  # 57
 start = parse_number("50")   # 50
 end = parse_number("100")    # 100

 percentage = (target - start) / (end - start)  # 0.14
 percentage = clamp(percentage, 0, 1)

 # Determinar lado (Colombia: impar=derecha, par=izquierda)
 is_odd = target % 2 == 1
 side = "RIGHT" if is_odd else "LEFT"

 Output:
 InterpolationResult(
     percentage=0.14,
     side="RIGHT",
     is_odd=True
 )

 Fase 5: GENERATE - Generar Coordenadas

 Archivo: generator.py

 Responsabilidad: Interpolar coordenadas sobre geometría del segmento

 Algoritmo (interpolación lineal simple):
 lat = start_lat + percentage * (end_lat - start_lat)
 lon = start_lon + percentage * (end_lon - start_lon)

 Nota: Para líneas multi-punto (futuro), usar Haversine para calcular distancias reales

 Fase 6: OFFSET - Ajustar Posición Lateral

 Archivo: generator.py (método apply_lateral_offset)

 Responsabilidad: Mover punto perpendicular a la calle (10m)

 Algoritmo:
 1. Calcular bearing (azimut) del segmento
 2. Ajustar bearing perpendicular: +90° (RIGHT) o -90° (LEFT)
 3. Calcular nueva posición usando offset_coordinate()

 Utilidades geográficas:
 - calculate_bearing(lat1, lon1, lat2, lon2) → azimut en grados
 - offset_coordinate(lat, lon, bearing, distance_m) → (new_lat, new_lon)

 Modelos de Datos

 Dataclasses Internos (models.py)

 @dataclass
 class AddressComponents:
     street_type: str
     street_name: str
     number_prefix: str
     number_suffix: Optional[str]
     raw_address: str

 @dataclass
 class StreetSegment:
     street_name: str
     start_number: str
     end_number: str
     start_lat: Decimal
     start_lon: Decimal
     end_lat: Decimal
     end_lon: Decimal
     city: str

 @dataclass
 class InterpolationResult:
     percentage: float
     side: Literal["LEFT", "RIGHT"]
     is_odd: bool

 @dataclass
 class GeocodingResult:
     success: bool
     latitude: Optional[float]
     longitude: Optional[float]
     accuracy: str
     side: Optional[Literal["LEFT", "RIGHT"]]
     matched_street: Optional[str]
     message: str
     components: Optional[AddressComponents] = None
     segment: Optional[StreetSegment] = None

 Schemas Pydantic (Opcional - schemas.py)

 class GeocodingRequest(BaseModel):
     address: str
     city: str
     region: str = "ANT"
     offset_distance: float = 10.0

 class GeocodingResponse(BaseModel):
     success: bool
     latitude: Optional[float]
     longitude: Optional[float]
     accuracy: str
     side: Optional[Literal["LEFT", "RIGHT"]]
     matched_street: Optional[str]
     message: str
     debug_info: Optional[dict] = None

 GeocodingService - Orquestador

 class GeocodingService:
     def __init__(self, db: AsyncSession, config: GeocodingConfig = None):
         self.db = db
         self.config = config or GeocodingConfig()
         self.parser = AddressParser()
         self.searcher = StreetSearcher(db)
         self.interpolator = PositionInterpolator()
         self.generator = CoordinateGenerator()

     async def geocode(
         self,
         address: str,
         city: str,
         region: str = "ANT",
         offset_distance: float = 10.0
     ) -> GeocodingResult:
         """Pipeline completo en 6 fases"""

         # Fase 1: PARSE
         components = self.parser.parse(address)
         if not components:
             return GeocodingResult(success=False, ...)

         # Fase 2: SEARCH
         candidates = await self.searcher.search_streets(
             street_name=components.street_name,
             city=city,
             region=region
         )
         if not candidates:
             return GeocodingResult(success=False, ...)

         # Fase 3: MATCH
         segment = await self.searcher.find_segment(
             candidates, components.number_prefix
         )
         if not segment:
             # Fallback: usar primer candidato
             segment = self._create_fallback_segment(candidates[0])

         # Fase 4: INTERPOLATE
         interp_result = self.interpolator.interpolate(
             components.number_prefix, segment
         )

         # Fase 5: GENERATE
         lat, lon = self.generator.generate_coordinates(
             segment, interp_result.percentage
         )

         # Fase 6: OFFSET
         final_lat, final_lon = self.generator.apply_lateral_offset(
             lat, lon, segment, interp_result.side, offset_distance
         )

         return GeocodingResult(
             success=True,
             latitude=final_lat,
             longitude=final_lon,
             accuracy="INTERPOLATED",
             side=interp_result.side,
             matched_street=segment.street_name,
             message="Successfully geocoded",
             components=components,
             segment=segment
         )

 Utilidades Matemáticas (utils.py)

 Funciones Clave

 def haversine_distance(lat1, lon1, lat2, lon2) -> float:
     """Distancia en metros entre dos puntos (fórmula Haversine)"""
     # R = 6371000 metros
     # Implementar fórmula estándar

 def calculate_bearing(lat1, lon1, lat2, lon2) -> float:
     """Calcular azimut inicial (0-360°)"""
     # Usar atan2 para calcular ángulo

 def offset_coordinate(lat, lon, bearing, distance_m) -> Tuple[float, float]:
     """Nueva coordenada a distancia y bearing desde origen"""
     # Fórmula de desplazamiento esférico

 Constantes Colombianas (constants.py)

 STREET_TYPE_ABBREVIATIONS = {
     "CALLE": "CL",
     "CARRERA": "KR",
     "AVENIDA": "AV",
     "DIAGONAL": "DG",
     "TRANSVERSAL": "TV",
     "CR": "KR",  # Normalizar CR → KR
 }

 STREET_TYPE_LONG_FORMS = {
     "CL": "CALLE",
     "KR": "CARRERA",
     "AV": "AVENIDA",
     # ...
 }

 Archivos Críticos a Crear

 Prioridad 1 (Sin dependencias DB)

 1. src/modules/geocoding/constants.py - Diccionarios de abreviaturas
 2. src/modules/geocoding/utils.py - Funciones matemáticas (Haversine, etc.)
 3. src/modules/geocoding/models.py - Dataclasses
 4. src/modules/geocoding/parser.py - Parseo de direcciones
 5. src/modules/geocoding/config.py - Configuración

 Prioridad 2 (Lógica core)

 6. src/modules/geocoding/interpolator.py - Cálculo de posición
 7. src/modules/geocoding/generator.py - Generación de coordenadas + offset

 Prioridad 3 (Integración DB)

 8. src/modules/geocoding/searcher.py - Búsqueda en tabla addresses (async)
 9. src/modules/geocoding/service.py - Orquestador principal
 10. src/modules/geocoding/init.py - Exports públicos

 Prioridad 4 (Opcional - API)

 11. src/modules/geocoding/schemas.py - Pydantic models
 12. src/modules/geocoding/router.py - FastAPI endpoints
 13. Modificar src/app.py - Registrar router

 Tests a Crear

 Tests Unitarios (sin DB)

 - tests/test_geocoding_parser.py - Parseo de diferentes formatos
 - tests/test_geocoding_utils.py - Funciones matemáticas
 - tests/test_geocoding_interpolator.py - Cálculo de posición
 - tests/test_geocoding_generator.py - Generación de coordenadas

 Tests de Integración (con DB)

 - tests/test_geocoding_searcher.py - Búsqueda en tabla addresses
 - tests/test_geocoding_service.py - Pipeline completo end-to-end

 Fixtures de Test

 # En conftest.py
 @pytest_asyncio.fixture
 async def sample_addresses(db_session: AsyncSession):
     addresses = [
         Address(
             street="KR 43", number="50",
             city="Jardín", region="ANT",
             latitude=Decimal("5.5900"), longitude=Decimal("-75.8200")
         ),
         Address(
             street="KR 43", number="100",
             city="Jardín", region="ANT",
             latitude=Decimal("5.5950"), longitude=Decimal("-75.8150")
         ),
     ]
     db_session.add_all(addresses)
     await db_session.commit()
     return addresses

 Consideraciones Especiales

 Campo number en Address

 - Tipo actual: String(50)
 - Formato observado: "13 247", "0 05" (espacio como separador)
 - Estrategia de parsing:
   - Extraer primera porción numérica: "13 247" → 13
   - Usar para comparación de rangos en Fase 3

 Normalización de Calles

 - Expandir abreviaturas: CR → KR
 - Construir nombre completo para búsqueda: street_type + " " + street_name
 - Ejemplo: KR + 43 → "KR 43"

 Manejo de Errores

 - Parse falla: Retornar success=False, accuracy="PARSE_FAILED"
 - No match de calle: Retornar accuracy="NO_STREET_MATCH"
 - No match de segmento: Usar fallback (primer candidato o centroide)
 - Excepciones DB: Capturar y retornar error genérico

 Fallbacks en Cascada

 1. Match exacto de segmento → INTERPOLATED
 2. Segmento más cercano → RANGE_MATCH
 3. Centroide de calle → STREET_CENTROID
 4. Centroide de ciudad → CITY_CENTROID
 5. Error → NO_MATCH

 Configuración (config.py)

 @dataclass
 class GeocodingConfig:
     max_search_results: int = 100
     default_offset_distance_m: float = 10.0
     fuzzy_search_threshold: float = 0.7

     # Niveles de precisión
     ACCURACY_INTERPOLATED = "INTERPOLATED"
     ACCURACY_RANGE_MATCH = "RANGE_MATCH"
     ACCURACY_STREET_CENTROID = "STREET_CENTROID"
     ACCURACY_NO_MATCH = "NO_MATCH"

 Integración con FastAPI (Opcional)

 Router

 # src/modules/geocoding/router.py
 router = APIRouter(prefix="/api/v1/geocoding", tags=["geocoding"])

 @router.post("/geocode", response_model=GeocodingResponse)
 async def geocode_address(
     request: GeocodingRequest,
     db: AsyncSession = Depends(get_db)
 ):
     service = GeocodingService(db)
     result = await service.geocode(
         address=request.address,
         city=request.city,
         region=request.region,
         offset_distance=request.offset_distance
     )
     return GeocodingResponse(...from result...)

 Registrar en app.py

 from src.modules.geocoding.router import router as geocoding_router
 app.include_router(geocoding_router)

 Performance Esperado

 - Parse: <1ms (regex en memoria)
 - Search: 10-50ms (query indexado, ~100 resultados)
 - Match: <5ms (sorting/iteración en Python)
 - Interpolate: <1ms (aritmética)
 - Generate: <1ms (funciones matemáticas)
 - Total: ~20-60ms por dirección

 Optimizaciones Futuras

 1. Caché de búsquedas - Redis para calles frecuentes
 2. Índices trigram - Para mejor fuzzy search:
 CREATE EXTENSION pg_trgm;
 CREATE INDEX idx_street_trgm ON addresses USING gin (street gin_trgm_ops);
 3. Batch geocoding - Endpoint para múltiples direcciones
 4. Interpolación geométrica - Considerar curvatura de calles (Shapely)

 Criterios de Éxito

 ✅ Sistema debe:
 1. Geocodificar "KR 43 # 57 49, Jardín" correctamente
 2. Manejar variaciones: "Carrera 43 # 57-49", "CR 43 # 57 49"
 3. Retornar coordenadas con precisión < 50 metros (depende de calidad de datos)
 4. Identificar lado correcto (izq/der basado en par/impar)
 5. Procesar en < 100ms (target)
 6. Manejar errores gracefully con mensajes claros

 Restricciones

 ❌ NO implementar:
 - Migraciones de base de datos (modelo Address ya existe)
 - PostGIS o funciones geométricas de PostgreSQL
 - UI/Frontend
 - Modificaciones a tabla addresses

 ✅ SÍ implementar:
 - Lógica pura de geocodificación
 - Cálculos matemáticos (Haversine)
 - Queries SQL async simples
 - Tests comprehensivos
 - Manejo robusto de errores

 Secuencia de Implementación

 1. Fase Foundation (sin DB):
   - Crear estructura de directorios
   - Implementar constants.py, utils.py, models.py, config.py
   - Implementar parser.py con tests
   - Tests unitarios para utils y parser
 2. Fase Core Logic (sin DB):
   - Implementar interpolator.py con tests
   - Implementar generator.py con tests
 3. Fase Database (con DB):
   - Implementar searcher.py con tests async
   - Implementar service.py (orquestador)
   - Tests de integración end-to-end
 4. Fase API (opcional):
   - Implementar schemas.py y router.py
   - Registrar en src/app.py
   - Tests de endpoints

 Notas Importantes

 - Async en todo: Seguir patrón existente con async/await
 - No leer antioquia.geojson: Archivo muy grande (244 MB), no necesario para implementación
 - Usar índices existentes: idx_addresses_full, idx_addresses_street, etc.
 - Parseo flexible: Campo number puede tener formatos variados
 - Commit explícito: SQLAlchemy 2.0 async requiere await db.commit() explícito (pero searcher solo lee, no modifica)