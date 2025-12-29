"""
Configuración y creación de la aplicación FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings

def create_app() -> FastAPI:
    """
    Factory para crear y configurar la aplicación FastAPI

    Returns:
        FastAPI: Instancia configurada de la aplicación
    """
    app = FastAPI(
        title="Georeference API",
        description="API para procesamiento de georreferenciación",
        version="0.1.0",
        debug=settings.DEBUG
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configurar según necesidades
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rutas básicas
    @app.get("/")
    async def root():
        """Ruta raíz de la API"""
        return {
            "message": "Georeference API",
            "version": "0.1.0",
            "status": "running",
            "environment": settings.ENVIRONMENT
        }

    @app.get("/health")
    async def health():
        """Endpoint de health check"""
        return {"status": "healthy"}

    # Aquí se pueden registrar más routers
    # from src.modules.example import router as example_router
    # app.include_router(example_router, prefix="/api/v1")

    return app

# Crear instancia de la aplicación
app = create_app()
