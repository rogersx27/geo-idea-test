"""
Entrypoint principal de la aplicación
"""
import uvicorn
from src.config.settings import settings
from src.app import create_app

def main():
    """Función principal para iniciar el servidor"""
    app = create_app()

    print(f"Iniciando servidor en {settings.HOST}:{settings.PORT}")
    print(f"Ambiente: {settings.ENVIRONMENT}")
    print(f"Debug: {settings.DEBUG}")

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    main()
