"""
Utilidades de validación para la configuración y datos.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def validate_config() -> bool:
    """
    Valida que la configuración sea correcta.
    
    Returns:
        True si la configuración es válida
    """
    try:
        from config.settings import settings
        
        # Validar credenciales de Azure AD
        required_azure_fields = [
            'azure_ad_client_id',
            'azure_ad_client_secret',
            'azure_ad_tenant_id',
            'azure_ad_resource'
        ]
        
        for field in required_azure_fields:
            if not getattr(settings, field, None):
                logger.error(f"Falta la configuración: {field}")
                return False
        
        # Validar configuración de base de datos
        required_db_fields = [
            'db_host',
            'db_user',
            'db_password',
            'db_name'
        ]
        
        for field in required_db_fields:
            if not getattr(settings, field, None):
                logger.error(f"Falta la configuración: {field}")
                return False
        
        # Validar configuración de API
        if not getattr(settings, 'api_base_url', None):
            logger.error("Falta la configuración: api_base_url")
            return False
        
        logger.info("Configuración validada correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error validando configuración: {e}")
        return False


def validate_entity_name(entity_name: str) -> bool:
    """
    Valida que el nombre de entidad sea válido.
    
    Args:
        entity_name: Nombre de la entidad
        
    Returns:
        True si el nombre es válido
    """
    from domain.constants import ENTITIES
    
    if entity_name in ENTITIES:
        return True
    
    logger.warning(f"Nombre de entidad no reconocido: {entity_name}")
    return False


