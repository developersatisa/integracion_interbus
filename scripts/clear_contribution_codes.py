# -*- coding: utf-8 -*-
"""
Script para borrar todos los registros de la entidad ContributionAccountCodeCCs en Dynamics 365.
"""
import logging
import sys
import json
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.token_service import AzureADTokenService
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def clear_contribution_codes():
    try:
        token_service = AzureADTokenService()
        dynamics_api = DynamicsAPIAdapter()
        
        logger.info("Obteniendo token de acceso...")
        access_token = token_service.get_access_token()
        
        entity_name = "ContributionAccountCodeCCs"
        
        # 1. Obtener todos los registros
        logger.info(f"Obteniendo todos los registros de {entity_name}...")
        # No usamos filtro de dataAreaId porque es una entidad global
        records = dynamics_api.get_entity_data(entity_name, access_token)
        
        if not records:
            logger.info(f"No hay registros para borrar en {entity_name}.")
            return

        logger.info(f"Se han encontrado {len(records)} registros para eliminar.")
        
        # 2. Borrar registros uno a uno
        success_count = 0
        error_count = 0
        
        logger.info("Analizando los primeros registros...")
        for i, record in enumerate(records[:10]):
            logger.info(f"Registro {i+1}: {json.dumps(record)}")

        for record in records:
            # Obtener valor de EQMCCC
            eqmccc = str(record.get('EQMCCC') or '').strip()
            
            if not eqmccc:
                logger.warning(f"Registro sin EQMCCC omitido: {record.get('RecId')}")
                continue
                
            try:
                logger.info(f"Intentando eliminar por EQMCCC: '{eqmccc}'...")
                dynamics_api.delete_entity_data(entity_name, access_token, eqmccc)
                success_count += 1
            except Exception as e:
                # No loguear el error completo si es muy largo, solo la primera línea
                error_msg = str(e).split('\n')[0]
                logger.error(f"Error eliminando {item_id}: {error_msg}")
                error_count += 1
            
            # Limitar para no saturar si hay miles de errores
            if error_count > 50:
                logger.error("Demasiados errores consecutivos. Abortando.")
                break
        
        logger.info(f"=== RESUMEN DE ELIMINACIÓN ===")
        logger.info(f"Total encontrados: {len(records)}")
        logger.info(f"Eliminados con éxito: {success_count}")
        logger.info(f"Errores: {error_count}")

    except Exception as e:
        logger.error(f"Error general: {e}")

if __name__ == "__main__":
    clear_contribution_codes()
