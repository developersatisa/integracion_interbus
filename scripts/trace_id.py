# -*- coding: utf-8 -*-
"""
Script de diagnóstico para rastrear un ID específico (038150001) en la integración.
"""
import logging
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.e03800_database_adapter import E03800DatabaseAdapter
from infrastructure.token_service import AzureADTokenService
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def trace_id(target_id):
    adapter = E03800DatabaseAdapter()
    token_service = AzureADTokenService()
    dynamics_api = DynamicsAPIAdapter()
    
    logger.info(f"=== RASTREANDO ID: {target_id} ===")
    
    # 1. Comprobar en e03800.empresas
    codiemp = target_id[:5] # Asumiendo que los primeros 5 son el codigop
    logger.info(f"1. Buscando empresa {codiemp} en e03800.empresas...")
    connection = adapter._get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM empresas WHERE codiemp = %s", (codiemp,))
    empresa = cursor.fetchone()
    if empresa:
        logger.info(f"   ✓ Empresa encontrada: {empresa['nombre']}")
    else:
        logger.error(f"   ✗ Empresa {codiemp} NO encontrada en e03800.empresas")
    
    # 2. Comprobar en WorkerPlaces (e03800_adapter)
    logger.info("2. Buscando en WorkerPlaces (e03800_adapter)...")
    wp_data = adapter.get_worker_places()
    found_wp = [item for item in wp_data if item['id'] == target_id]
    if found_wp:
        logger.info(f"   ✓ Encontrado en WorkerPlaces local: {found_wp[0]}")
    else:
        logger.error(f"   ✗ NO encontrado en WorkerPlaces local")
        
    # 3. Comprobar en ContributionAccountCodeCCs (e03800_adapter)
    logger.info("3. Buscando en ContributionAccountCodeCCs (e03800_adapter)...")
    cc_data = adapter.get_contribution_account_code_ccs()
    found_cc = [item for item in cc_data if target_id in item['id']]
    if found_cc:
        logger.info(f"   ✓ Encontrado en ContributionAccountCodeCCs local: {found_cc[0]}")
    else:
        logger.error(f"   ✗ NO encontrado en ContributionAccountCodeCCs local")

    # 4. Comprobar en Dynamics 365
    logger.info("4. Consultando Dynamics 365...")
    access_token = token_service.get_access_token()
    
    # Buscar el WorkerPlace en Dynamics
    logger.info(f"   Buscando WorkerPlace {target_id} en Dynamics...")
    filter_exp = f"EQMWorkerPlaceID eq '{target_id}' and dataAreaId eq 'itb'"
    dynamics_wp = dynamics_api.get_entity_data("WorkerPlaces", access_token, filter_expression=filter_exp)
    
    if dynamics_wp:
        logger.info(f"   ✓ Encontrado en Dynamics: {dynamics_wp[0]}")
    else:
        logger.error(f"   ✗ NO encontrado en Dynamics (itb)")
        
        # Buscar sin filtro de empresa por si acaso
        logger.info("   Buscando en Dynamics (todas las empresas)...")
        dynamics_wp_all = dynamics_api.get_entity_data("WorkerPlaces", access_token, filter_expression=f"EQMWorkerPlaceID eq '{target_id}'")
        if dynamics_wp_all:
            logger.info(f"   ⚠ Encontrado en OTRA empresa: {dynamics_wp_all[0].get('dataAreaId')}")
        else:
            logger.error("   ✗ NO encontrado en ninguna empresa")

if __name__ == "__main__":
    trace_id("038030002")
