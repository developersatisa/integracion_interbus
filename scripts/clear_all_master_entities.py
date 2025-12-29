# -*- coding: utf-8 -*-
"""
Script para borrar todos los registros de todas las entidades maestras en Dynamics 365.
"""
import logging
import sys
import json
import urllib.parse
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.token_service import AzureADTokenService
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from config.logging_config import setup_logging
from domain.constants import ENTITIES

setup_logging()
logger = logging.getLogger(__name__)

def get_key_field(entity_name):
    """Devuelve el campo clave para cada entidad"""
    mapping = {
        'HolidaysAbsencesGroupATISAs': 'EQMHolidaysAbsencesGroupATISAId',
        'IncidentGroupATISAs': 'EQMIncidentGroupATISAId',
        'AdvanceGroupATISAs': 'EQMAdvanceGroupATISAId',
        'LibrariesGroupATISAs': 'EQMLibrariesGroupATISAId',
        'LeaveGroupATISAs': 'EQMLeaveGroupATISAId',
        'HighsLowsChanges': 'EQMHighsLowsChangesID',
        'VacationCalenders': 'EQMVacationCalenderId',
        'CompanyATISAs': 'EQMCompanyIdATISA',
        'WorkerPlaces': 'EQMWorkerPlaceID',
        'VacationBalances': 'EQMVacationBalanceId',
        'ContributionAccountCodeCCs': 'EQMCCC'
    }
    return mapping.get(entity_name, 'EQMHolidaysAbsencesGroupATISAId')

def clear_all_entities():
    try:
        token_service = AzureADTokenService()
        dynamics_api = DynamicsAPIAdapter()
        
        logger.info("Obteniendo token de acceso...")
        access_token = token_service.get_access_token()
        
        # Invertir el orden para borrar dependencias si las hubiera (opcional)
        # Por ahora usamos el orden definido en constantes
        for entity_name in ENTITIES:
            logger.info("\n" + "="*60)
            logger.info(f"LIMPIANDO ENTIDAD: {entity_name}")
            logger.info("="*60)
            
            key_field = get_key_field(entity_name)
            
            # 1. Obtener todos los registros
            try:
                logger.info(f"Obteniendo registros de {entity_name}...")
                records = dynamics_api.get_entity_data(entity_name, access_token)
            except Exception as e:
                logger.error(f"Error obteniendo datos de {entity_name}: {e}")
                continue
            
            if not records:
                logger.info(f"No hay registros para borrar en {entity_name}.")
                continue

            logger.info(f"Se han encontrado {len(records)} registros para eliminar.")
            
            # 2. Borrar registros uno a uno
            success_count = 0
            error_count = 0
            
            for record in records:
                # Obtener el ID del registro
                item_id = str(record.get(key_field) or '').strip()
                data_area_id = str(record.get('dataAreaId') or 'itb').strip()
                
                if not item_id:
                    # Fallback para ContributionAccountCodeCCs si EQMCCC está vacío por alguna razón
                    if entity_name == 'ContributionAccountCodeCCs':
                        item_id = str(record.get('RecId') or '')
                    
                    if not item_id:
                        logger.warning(f"Registro sin ID omitido en {entity_name}")
                        continue
                    
                try:
                    # Usar el adaptador para borrar
                    # El adaptador ya maneja las particularidades de CCC y VacationBalances
                    dynamics_api.delete_entity_data(entity_name, access_token, item_id, key_field=key_field, data_area_id=data_area_id)
                    success_count += 1
                except Exception as e:
                    error_msg = str(e).split('\n')[0]
                    logger.error(f"Error eliminando {item_id} en {entity_name}: {error_msg}")
                    error_count += 1
                
                # Limitar errores por entidad
               
            
            logger.info(f"--- RESUMEN {entity_name} ---")
            logger.info(f"Encontrados: {len(records)}")
            logger.info(f"Eliminados: {success_count}")
            logger.info(f"Errores: {error_count}")

        logger.info("\n" + "="*60)
        logger.info("PROCESO DE LIMPIEZA GLOBAL FINALIZADO")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Error general: {e}")

if __name__ == "__main__":
    # Confirmación de seguridad
    print("¡ADVERTENCIA! Este script borrará TODOS los registros de las entidades maestras en Dynamics 365.")
    confirm = input("¿Estás seguro de que deseas continuar? (s/n): ")
    
    if confirm.lower() == 's':
        clear_all_entities()
    else:
        print("Operación cancelada.")
