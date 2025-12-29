"""
Configuración de la aplicación usando variables de entorno
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    """Clase para manejar la configuración de la aplicación"""

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "myapp_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")

    # API Keys
    API_KEY: Optional[str] = os.getenv("API_KEY")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")

    # Other Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def database_url(self) -> str:
        """Construye la URL de conexión a la base de datos"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# Instancia global de configuración
settings = Settings()
