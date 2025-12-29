# -*- coding: utf-8 -*-
"""
Script para listar los registros de WorkerPlaces en Dynamics 365.
Utiliza los filtros necesarios para ver los datos de la empresa 'itb'.
"""
import logging
import sys
import json
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from config.logging_config import setup_logging
from infrastructure.token_service import AzureADTokenService
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

def list_worker_places():
    try:
        token_service = AzureADTokenService()
        dynamics_api = DynamicsAPIAdapter()
        
        logger.info("Obteniendo token de acceso...")
        access_token = token_service.get_access_token()
        
        entity_name = "WorkerPlaces"
        filter_exp = "dataAreaId eq 'itb'"
        
        logger.info(f"Consultando {entity_name} con filtro: {filter_exp}...")
        # get_entity_data ya incluye company=itb internamente tras la reversión del cambio
        data = dynamics_api.get_entity_data(entity_name, access_token, filter_expression=filter_exp)
        
        logger.info(f"✓ Se encontraron {len(data)} registros en Dynamics 365 para la empresa 'itb'")
        
        if data:
            print("\n" + "="*80)
            print(f"{'ID (EQMWorkerPlaceID)':<25} | {'Descripción (Description)':<40} | {'Empresa'}")
            print("-" * 80)
            for record in data[:20]: # Mostrar los primeros 20
                wp_id = record.get('EQMWorkerPlaceID', 'N/A')
                desc = record.get('Description', 'N/A')
                area = record.get('dataAreaId', 'N/A')
                print(f"{wp_id:<25} | {desc[:40]:<40} | {area}")
            
            if len(data) > 20:
                print(f"\n... y {len(data) - 20} registros más.")
            print("="*80)
            
            # Guardar muestra en un archivo para que el usuario pueda verla completa si quiere
            with open('worker_places_sample.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Muestra completa guardada en 'worker_places_sample.json'")
        else:
            logger.warning("No se devolvieron registros. Esto confirma que sin los parámetros correctos la API devuelve vacío.")

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    list_worker_places()
