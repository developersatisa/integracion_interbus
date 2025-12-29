"""
Configuración de la aplicación usando pydantic-settings para gestión segura de variables de entorno.
"""
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Azure AD Credentials
    azure_ad_client_id: str
    azure_ad_client_secret: str
    azure_ad_tenant_id: str
    azure_ad_resource: str
    
    # Database Configuration
    db_host: str
    db_port: int = 3306
    db_user: str
    db_password: str
    db_name: str
    
    # API Configuration
    api_base_url: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Verificar si existe el archivo .env antes de cargar settings
if not os.path.exists('.env'):
    print("⚠️  ERROR: No se encontró el archivo .env")
    print("\nPara configurar el entorno:")
    print("1. Ejecuta: python3 scripts/setup_env.py")
    print("2. O copia manualmente: cp env.example .env")
    print("3. Edita .env con tus credenciales")
    exit(1)

settings = Settings()

