"""
Ejemplo de uso de la aplicación de sincronización.
Demuestra cómo usar los casos de uso de forma independiente.
"""
import logging
from domain.constants import ENTITIES
from infrastructure.token_service import AzureADTokenService
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from infrastructure.database_adapter import MySQLDatabaseAdapter
from application.use_cases import SyncDynamicsEntityUseCase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_sync_single_entity():
    """Ejemplo de sincronización de una única entidad."""
    logger.info("=== Ejemplo: Sincronizar una entidad ===")
    
    # Setup
    token_service = AzureADTokenService()
    dynamics_api = DynamicsAPIAdapter()
    database_adapter = MySQLDatabaseAdapter()
    
    # Inicializar base de datos
    database_adapter.initialize_database()
    
    # Crear caso de uso
    use_case = SyncDynamicsEntityUseCase(
        token_service,
        dynamics_api,
        database_adapter
    )
    
    # Ejecutar sincronización
    result = use_case.execute('CompanyATISAs')
    
    logger.info(f"Resultado: {result}")


def example_check_token():
    """Ejemplo de verificación de token."""
    logger.info("=== Ejemplo: Verificar token ===")
    
    token_service = AzureADTokenService()
    
    try:
        token = token_service.get_access_token()
        logger.info(f"Token obtenido: {token[:50]}...")
    except Exception as e:
        logger.error(f"Error obteniendo token: {e}")


if __name__ == "__main__":
    # Descomentar para ejecutar ejemplos
    
    # example_check_token()
    # example_sync_single_entity()
    
    logger.info("Ver ejemplos/sync_example.py para más información")


