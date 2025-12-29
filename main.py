# -*- coding: utf-8 -*-
"""
Punto de entrada principal de la aplicación.
Integra todas las capas siguiendo arquitectura hexagonal y principios SOLID.
"""
import logging
import sys
import json

from config.settings import settings
from config.logging_config import setup_logging
from domain.ports import TokenRepository, DynamicsAPIAdapter, DatabaseAdapter
from domain.constants import ENTITIES
from infrastructure.token_service import AzureADTokenService
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from infrastructure.database_adapter import MySQLDatabaseAdapter
from application.use_cases import SyncAllEntitiesUseCase, SyncDynamicsEntityUseCase
from application.bidirectional_sync_use_case import BidirectionalSyncUseCase
from application.employee_modifications_use_case import SyncEmployeeModificationsUseCase
from infrastructure.employee_modifications_adapter import EmployeeModificationsAdapter
from infrastructure.e03800_database_adapter import E03800DatabaseAdapter
from utils.validators import validate_config, validate_entity_name


# Configurar logging
logger = setup_logging()

# Lista de entidades a sincronizar
ENTITIES_TO_SYNC = ENTITIES


def setup_dependencies() -> tuple:
    """
    Configura las dependencias siguiendo el principio de inversión de dependencias (DIP).
    
    Returns:
        Tupla con las instancias de los adaptadores
    """
    logger.info("Configurando dependencias...")
    
    # Adaptadores de infraestructura
    token_service = AzureADTokenService()
    dynamics_api = DynamicsAPIAdapter()
    database_adapter = MySQLDatabaseAdapter()
    
    return token_service, dynamics_api, database_adapter


def main():
    """Función principal."""
    logger.info("="*60)
    logger.info("INICIANDO APLICACIÓN DE SINCRONIZACIÓN DE DYNAMICS 365")
    logger.info("="*60)
    
    try:
        # Validar configuración
        logger.info("Validando configuración...")
        if not validate_config():
            logger.error("Error en la configuración. Verifica el archivo .env")
            sys.exit(1)
        
        # Setup de dependencias
        logger.info("Configurando dependencias...")
        token_service, dynamics_api, database_adapter = setup_dependencies()
        
        # Inicializar base de datos
        logger.info("Inicializando base de datos...")
        database_adapter.initialize_database()
        
        # Entidades con sincronización bidireccional especial
        # El orden es IMPORTANTE: WorkerPlaces debe ir antes que ContributionAccountCodeCCs
        BIDIRECTIONAL_ENTITIES = [
            'CompanyATISAs', 
            'WorkerPlaces', 
            'ContributionAccountCodeCCs', 
            'HolidaysAbsencesGroupATISAs', 
            'VacationBalances',
            'IncidentGroupATISAs', 
            'AdvanceGroupATISAs', 
            'LibrariesGroupATISAs', 
            'LeaveGroupATISAs', 
            'HighsLowsChanges', 
            'VacationCalenders'
        ]

        # Separar entidades con lógica especial
        standard_entities = [e for e in ENTITIES_TO_SYNC if e not in BIDIRECTIONAL_ENTITIES]

        # 1. Sincronización bidireccional para entidades especiales
        for entity in BIDIRECTIONAL_ENTITIES:
            if entity in ENTITIES_TO_SYNC:
                logger.info("\n" + "="*60)
                logger.info(f"SINCRONIZACIÓN BIDIRECCIONAL ({entity})")
                logger.info("="*60)

                bidirectional_use_case = BidirectionalSyncUseCase(
                    token_service,
                    dynamics_api,
                    database_adapter
                )

                result = bidirectional_use_case.execute(entity)

                if result['success']:
                    logger.info(f"✓ {result['entity']}: Sincronización bidireccional completada")
                    logger.info(f"  - e03800: {result['e03800_count']} registros")
                    logger.info(f"  - Dynamics antes: {result['dynamics_initial_count']} registros")
                    logger.info(f"  - Dynamics después: {result['dynamics_final_count']} registros")
                    logger.info(f"  - Creados: {len(result['actions_taken']['created'])}")
                    logger.info(f"  - Eliminados: {len(result['actions_taken']['deleted'])}")
                    logger.info(f"  - Sin cambios: {len(result['actions_taken']['unchanged'])}")
                else:
                    logger.error(f"✗ {result['entity']}: Error - {result.get('error', 'Desconocido')}")
        
        # 2. Sincronización estándar para el resto de entidades
        if standard_entities:
            logger.info("\n" + "="*60)
            logger.info(f"SINCRONIZACIÓN ESTÁNDAR ({len(standard_entities)} entidades)")
            logger.info("="*60)
            
            sync_all_use_case = SyncAllEntitiesUseCase(
                token_service,
                dynamics_api,
                database_adapter
            )
            
            results = sync_all_use_case.execute(standard_entities)
            
            # Mostrar resultados
            success_count = 0
            failed_count = 0
            
            for result in results:
                if result['success']:
                    success_count += 1
                    logger.info(
                        f"✓ {result['entity']}: {result['records_synced']} registros sincronizados "
                        f"(Total: {result['records_count']})"
                    )
                else:
                    failed_count += 1
                    logger.error(
                        f"✗ {result['entity']}: Error - {result.get('error', 'Desconocido')}"
                    )
        
        logger.info("\n" + "="*60)
        logger.info("SINCRONIZACIÓN COMPLETADA")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error en la ejecución: {e}", exc_info=True)
        sys.exit(1)


def test_employee_modifications():
    """
    Función de prueba para conectar con el endpoint EmployeeModifications
    y visualizar los datos que devuelve.
    """
    logger.info("="*60)
    logger.info("PRUEBA DE CONEXIÓN: EmployeeModifications")
    logger.info("="*60)
    
    try:
        # Validar configuración
        logger.info("Validando configuración...")
        if not validate_config():
            logger.error("Error en la configuración. Verifica el archivo .env")
            sys.exit(1)
        
        # Setup de dependencias
        logger.info("Configurando dependencias...")
        token_service, dynamics_api, database_adapter = setup_dependencies()
        
        # Obtener token de acceso
        logger.info("Obteniendo token de acceso de Azure AD...")
        access_token = token_service.get_access_token()
        logger.info("✓ Token obtenido correctamente")
        
        # Realizar llamada al endpoint EmployeeModifications
        logger.info("\n" + "-"*60)
        logger.info("Conectando con endpoint: /data/EmployeeModifications")
        logger.info("-"*60)
        
        entity_name = "EmployeeModifications"
        employee_data = dynamics_api.get_entity_data(entity_name, access_token)
        
        # Mostrar resultados
        logger.info("\n" + "="*60)
        logger.info("RESULTADOS DE LA CONEXIÓN")
        logger.info("="*60)
        logger.info(f"✓ Conexión exitosa con {entity_name}")
        logger.info(f"✓ Total de registros obtenidos: {len(employee_data)}")
        
        if employee_data:
            # Mostrar estructura del primer registro
            logger.info("\n" + "-"*60)
            logger.info("ESTRUCTURA DEL PRIMER REGISTRO:")
            logger.info("-"*60)
            first_record = employee_data[0]
            logger.info(json.dumps(first_record, indent=2, ensure_ascii=False))
            
            # Mostrar campos disponibles
            logger.info("\n" + "-"*60)
            logger.info("CAMPOS DISPONIBLES EN LOS REGISTROS:")
            logger.info("-"*60)
            all_fields = set()
            for record in employee_data:
                all_fields.update(record.keys())
            
            for field in sorted(all_fields):
                logger.info(f"  - {field}")
            
            # Mostrar muestra de registros (primeros 3)
            logger.info("\n" + "-"*60)
            logger.info(f"MUESTRA DE REGISTROS (primeros {min(3, len(employee_data))} de {len(employee_data)}):")
            logger.info("-"*60)
            for idx, record in enumerate(employee_data[:3], 1):
                logger.info(f"\n--- Registro {idx} ---")
                logger.info(json.dumps(record, indent=2, ensure_ascii=False))
            
            if len(employee_data) > 3:
                logger.info(f"\n... y {len(employee_data) - 3} registros más")
        else:
            logger.warning("⚠ No se obtuvieron registros del endpoint")
        
        logger.info("\n" + "="*60)
        logger.info("PRUEBA COMPLETADA")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"✗ Error en la prueba: {e}", exc_info=True)
        sys.exit(1)


def sync_employee_modifications(limit: int = None):
    """
    Sincroniza registros de EmployeeModifications desde Dynamics 365.
    
    Args:
        limit: Límite de registros a procesar (None para todos)
    """
    logger.info("="*60)
    logger.info("SINCRONIZACIÓN DE EMPLOYEE MODIFICATIONS")
    logger.info("="*60)
    
    try:
        # Validar configuración
        logger.info("Validando configuración...")
        if not validate_config():
            logger.error("Error en la configuración. Verifica el archivo .env")
            sys.exit(1)
        
        # Setup de dependencias
        logger.info("Configurando dependencias...")
        token_service, dynamics_api, database_adapter = setup_dependencies()
        
        # Obtener token de acceso
        logger.info("Obteniendo token de acceso de Azure AD...")
        access_token = token_service.get_access_token()
        logger.info("✓ Token obtenido correctamente")
        
        # Crear adaptadores específicos
        employee_adapter = EmployeeModificationsAdapter()
        e03800_adapter = E03800DatabaseAdapter()
        
        # Crear caso de uso
        use_case = SyncEmployeeModificationsUseCase(
            dynamics_api,
            employee_adapter,
            e03800_adapter
        )
        
        # Ejecutar sincronización
        logger.info("\n" + "-"*60)
        logger.info("Iniciando procesamiento de registros...")
        logger.info("-"*60)
        
        if limit:
            logger.info(f"Procesando solo los primeros {limit} registros")
        
        stats = use_case.sync(access_token, limit)
        
        # Mostrar resultados
        logger.info("\n" + "="*60)
        logger.info("RESULTADOS DE LA SINCRONIZACIÓN")
        logger.info("="*60)
        logger.info(f"Total de registros: {stats['total']}")
        logger.info(f"✓ Procesados exitosamente: {stats['processed']}")
        logger.info(f"⊘ Omitidos: {stats['skipped']}")
        logger.info(f"✗ Errores: {stats['errors']}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error en la sincronización: {e}", exc_info=True)
        sys.exit(1)


def sync_single_entity(entity_name: str):
    """Sincroniza una única entidad."""
    logger.info(f"Iniciando sincronización de {entity_name}...")
    
    try:
        # Validar configuración
        if not validate_config():
            logger.error("Error en la configuración. Verifica el archivo .env")
            sys.exit(1)
        
        # Validar nombre de entidad
        if not validate_entity_name(entity_name):
            logger.error(f"Nombre de entidad no válido: {entity_name}")
            logger.info(f"Entidades disponibles: {', '.join(ENTITIES)}")
            sys.exit(1)
        
        token_service, dynamics_api, database_adapter = setup_dependencies()
        
        # Inicializar base de datos
        database_adapter.initialize_database()
        
        # Entidades con sincronización bidireccional
        BIDIRECTIONAL_ENTITIES = [
            'CompanyATISAs', 
            'WorkerPlaces', 
            'ContributionAccountCodeCCs', 
            'HolidaysAbsencesGroupATISAs', 
            'VacationBalances',
            'IncidentGroupATISAs', 
            'AdvanceGroupATISAs', 
            'LibrariesGroupATISAs', 
            'LeaveGroupATISAs', 
            'HighsLowsChanges', 
            'VacationCalenders'
        ]
        
        # Decidir qué caso de uso usar
        if entity_name in BIDIRECTIONAL_ENTITIES:
            logger.info("Usando sincronización bidireccional...")
            use_case = BidirectionalSyncUseCase(
                token_service,
                dynamics_api,
                database_adapter
            )
            result = use_case.execute(entity_name)
            
            if result['success']:
                logger.info(f"✓ {result['entity']}: Sincronización bidireccional completada")
                logger.info(f"  - Creados: {len(result['actions_taken']['created'])}")
                logger.info(f"  - Eliminados: {len(result['actions_taken']['deleted'])}")
                logger.info(f"  - Sin cambios: {len(result['actions_taken']['unchanged'])}")
            else:
                logger.error(f"✗ {result['entity']}: Error - {result.get('error', 'Desconocido')}")
        else:
            # Sincronización estándar
            logger.info("Usando sincronización estándar...")
            sync_use_case = SyncDynamicsEntityUseCase(
                token_service,
                dynamics_api,
                database_adapter
            )
            result = sync_use_case.execute(entity_name)
            
            if result['success']:
                logger.info(
                    f"✓ {result['entity']}: {result['records_synced']} registros sincronizados"
                )
            else:
                logger.error(
                    f"✗ {result['entity']}: Error - {result.get('error', 'Desconocido')}"
                )
        
    except Exception as e:
        logger.error(f"Error sincronizando {entity_name}: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        # Comando especial para probar EmployeeModifications
        if command == "test-employee-modifications":
            test_employee_modifications()
        # Comando para sincronizar EmployeeModifications
        elif command == "sync-employee-modifications":
            # Opcional: segundo argumento es el límite de registros
            limit = None
            if len(sys.argv) > 2:
                try:
                    limit = int(sys.argv[2])
                except ValueError:
                    logger.warning(f"Límite inválido: {sys.argv[2]}. Procesando todos los registros.")
            sync_employee_modifications(limit)
        else:
            # Sincronizar una entidad específica
            entity_name = command
            sync_single_entity(entity_name)
    else:
        # Sincronizar todas las entidades
        main()

