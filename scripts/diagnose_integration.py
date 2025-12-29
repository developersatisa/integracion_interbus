# -*- coding: utf-8 -*-
"""
Script de diagnóstico para la integración bidireccional con Dynamics 365.
Prueba cada componente de forma independiente para identificar problemas.
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
from infrastructure.database_adapter import MySQLDatabaseAdapter
from infrastructure.e03800_database_adapter import E03800DatabaseAdapter

# Configurar logging
logger = setup_logging()


def test_configuration():
    """Prueba 1: Verificar configuración"""
    logger.info("\n" + "="*60)
    logger.info("PRUEBA 1: VERIFICACIÓN DE CONFIGURACIÓN")
    logger.info("="*60)
    
    try:
        logger.info(f"✓ Azure AD Client ID: {settings.azure_ad_client_id[:10]}...")
        logger.info(f"✓ Azure AD Tenant ID: {settings.azure_ad_tenant_id[:10]}...")
        logger.info(f"✓ Azure AD Resource: {settings.azure_ad_resource}")
        logger.info(f"✓ API Base URL: {settings.api_base_url}")
        logger.info(f"✓ DB Host: {settings.db_host}")
        logger.info(f"✓ DB Port: {settings.db_port}")
        logger.info(f"✓ DB Name: {settings.db_name}")
        logger.info(f"✓ DB User: {settings.db_user}")
        return True
    except Exception as e:
        logger.error(f"✗ Error en configuración: {e}")
        return False


def test_token_acquisition():
    """Prueba 2: Obtener token de Azure AD"""
    logger.info("\n" + "="*60)
    logger.info("PRUEBA 2: OBTENCIÓN DE TOKEN DE AZURE AD")
    logger.info("="*60)
    
    try:
        token_service = AzureADTokenService()
        access_token = token_service.get_access_token()
        
        if access_token:
            logger.info(f"✓ Token obtenido correctamente (longitud: {len(access_token)})")
            logger.info(f"✓ Primeros caracteres: {access_token[:50]}...")
            return access_token
        else:
            logger.error("✗ No se pudo obtener el token")
            return None
    except Exception as e:
        logger.error(f"✗ Error obteniendo token: {e}", exc_info=True)
        return None


def test_dynamics_connection(access_token):
    """Prueba 3: Conectar con Dynamics 365"""
    logger.info("\n" + "="*60)
    logger.info("PRUEBA 3: CONEXIÓN CON DYNAMICS 365")
    logger.info("="*60)
    
    if not access_token:
        logger.error("✗ No hay token disponible, saltando prueba")
        return False
    
    try:
        dynamics_api = DynamicsAPIAdapter()
        
        # Probar con una entidad simple
        test_entity = "HolidaysAbsencesGroupATISAs"
        logger.info(f"Probando obtener datos de: {test_entity}")
        
        data = dynamics_api.get_entity_data(test_entity, access_token)
        
        logger.info(f"✓ Conexión exitosa con Dynamics 365")
        logger.info(f"✓ Registros obtenidos de {test_entity}: {len(data)}")
        
        if data:
            logger.info(f"\nPrimer registro:")
            logger.info(json.dumps(data[0], indent=2, ensure_ascii=False))
        
        return True
    except Exception as e:
        logger.error(f"✗ Error conectando con Dynamics 365: {e}", exc_info=True)
        return False


def test_e03800_connection():
    """Prueba 4: Conectar con base de datos e03800"""
    logger.info("\n" + "="*60)
    logger.info("PRUEBA 4: CONEXIÓN CON BASE DE DATOS E03800")
    logger.info("="*60)
    
    try:
        e03800_adapter = E03800DatabaseAdapter()
        
        # Probar obtener datos de gruposervicios
        logger.info("Probando obtener datos de gruposervicios (id_servicios=30)...")
        data = e03800_adapter.get_gruposervicios_by_service(30)
        
        logger.info(f"✓ Conexión exitosa con e03800")
        logger.info(f"✓ Registros obtenidos: {len(data)}")
        
        if data:
            logger.info(f"\nPrimeros 3 registros:")
            for i, record in enumerate(data[:3], 1):
                logger.info(f"  {i}. ID: {record['id']}, Nombre: {record['nombre']}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Error conectando con e03800: {e}", exc_info=True)
        return False


def test_interbus_365_connection():
    """Prueba 5: Conectar con base de datos interbus_365"""
    logger.info("\n" + "="*60)
    logger.info("PRUEBA 5: CONEXIÓN CON BASE DE DATOS INTERBUS_365")
    logger.info("="*60)
    
    try:
        db_adapter = MySQLDatabaseAdapter()
        
        # Verificar que la tabla existe
        logger.info("Verificando tabla dynamic_entities...")
        db_adapter.initialize_database()
        
        logger.info(f"✓ Conexión exitosa con interbus_365")
        logger.info(f"✓ Tabla dynamic_entities verificada")
        
        return True
    except Exception as e:
        logger.error(f"✗ Error conectando con interbus_365: {e}", exc_info=True)
        return False


def test_bidirectional_sync_logic(access_token):
    """Prueba 6: Lógica de sincronización bidireccional"""
    logger.info("\n" + "="*60)
    logger.info("PRUEBA 6: LÓGICA DE SINCRONIZACIÓN BIDIRECCIONAL")
    logger.info("="*60)
    
    if not access_token:
        logger.error("✗ No hay token disponible, saltando prueba")
        return False
    
    try:
        # Obtener datos de ambas fuentes
        dynamics_api = DynamicsAPIAdapter()
        e03800_adapter = E03800DatabaseAdapter()
        
        entity_name = "HolidaysAbsencesGroupATISAs"
        
        logger.info(f"\nObteniendo datos de e03800...")
        e03800_data = e03800_adapter.get_gruposervicios_by_service(30)
        logger.info(f"✓ e03800: {len(e03800_data)} registros")
        
        logger.info(f"\nObteniendo datos de Dynamics 365...")
        dynamics_data = dynamics_api.get_entity_data(entity_name, access_token)
        logger.info(f"✓ Dynamics 365: {len(dynamics_data)} registros")
        
        # Comparar IDs
        e03800_ids = set([str(item['id']) for item in e03800_data])
        dynamics_ids = set()
        
        for record in dynamics_data:
            if 'EQMHolidaysAbsencesGroupATISAId' in record:
                dynamics_ids.add(str(record['EQMHolidaysAbsencesGroupATISAId']))
        
        logger.info(f"\n📊 Análisis de datos:")
        logger.info(f"  IDs en e03800: {sorted(e03800_ids)}")
        logger.info(f"  IDs en Dynamics: {sorted(dynamics_ids)}")
        
        # Calcular diferencias
        to_create = e03800_ids - dynamics_ids
        to_delete = dynamics_ids - e03800_ids
        unchanged = e03800_ids & dynamics_ids
        
        logger.info(f"\n📋 Acciones necesarias:")
        logger.info(f"  ➕ Crear en Dynamics: {len(to_create)} registros")
        if to_create:
            logger.info(f"     IDs: {sorted(to_create)}")
        
        logger.info(f"  ❌ Eliminar de Dynamics: {len(to_delete)} registros")
        if to_delete:
            logger.info(f"     IDs: {sorted(to_delete)}")
        
        logger.info(f"  ✓ Sin cambios: {len(unchanged)} registros")
        
        return True
    except Exception as e:
        logger.error(f"✗ Error en lógica de sincronización: {e}", exc_info=True)
        return False


def test_all_bidirectional_entities(access_token):
    """Prueba 7: Verificar todas las entidades bidireccionales"""
    logger.info("\n" + "="*60)
    logger.info("PRUEBA 7: VERIFICACIÓN DE TODAS LAS ENTIDADES BIDIRECCIONALES")
    logger.info("="*60)
    
    if not access_token:
        logger.error("✗ No hay token disponible, saltando prueba")
        return False
    
    entities_config = {
        'CompanyATISAs': ('get_empresas', None),
        'WorkerPlaces': ('get_worker_places', None),
        'ContributionAccountCodeCCs': ('get_contribution_account_code_ccs', None),
        'HolidaysAbsencesGroupATISAs': ('get_gruposervicios_by_service', 30),
        'IncidentGroupATISAs': ('get_gruposervicios_by_service', 10),
        'AdvanceGroupATISAs': ('get_gruposervicios_by_service', 20),
        'LibrariesGroupATISAs': ('get_gruposervicios_by_service', 80),
        'LeaveGroupATISAs': ('get_gruposervicios_by_service', 100),
        'HighsLowsChanges': ('get_gruposervicios_by_service', 110),
        'VacationCalenders': ('get_vacation_calendars_current_year', None),
    }
    
    try:
        dynamics_api = DynamicsAPIAdapter()
        e03800_adapter = E03800DatabaseAdapter()
        
        results = []
        
        for entity_name, (method_name, param) in entities_config.items():
            logger.info(f"\n--- {entity_name} ---")
            
            try:
                # Obtener datos de e03800
                method = getattr(e03800_adapter, method_name)
                if param is not None:
                    e03800_data = method(param)
                else:
                    e03800_data = method()
                
                # Obtener datos de Dynamics
                dynamics_data = dynamics_api.get_entity_data(entity_name, access_token)
                
                logger.info(f"  e03800: {len(e03800_data)} registros")
                logger.info(f"  Dynamics: {len(dynamics_data)} registros")
                
                # Si es la entidad de empresas, mostrar los primeros CIFs
                if entity_name == 'CompanyATISAs' and e03800_data:
                    logger.info("  🔍 Muestra de CIFs en e03800:")
                    for emp in e03800_data[:5]:
                        logger.info(f"    - {emp['id']}: {emp['nombre']} (CIF: {emp.get('cif', 'N/A')})")
                
                results.append({
                    'entity': entity_name,
                    'e03800_count': len(e03800_data),
                    'dynamics_count': len(dynamics_data),
                    'status': 'OK'
                })
                
            except Exception as e:
                logger.error(f"  ✗ Error: {e}")
                results.append({
                    'entity': entity_name,
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        # Resumen
        logger.info(f"\n📊 RESUMEN:")
        logger.info(f"{'Entidad':<35} {'e03800':<10} {'Dynamics':<10} {'Estado'}")
        logger.info("-" * 70)
        for result in results:
            if result['status'] == 'OK':
                logger.info(
                    f"{result['entity']:<35} "
                    f"{result['e03800_count']:<10} "
                    f"{result['dynamics_count']:<10} "
                    f"✓"
                )
            else:
                logger.info(
                    f"{result['entity']:<35} "
                    f"{'ERROR':<10} "
                    f"{'ERROR':<10} "
                    f"✗ {result.get('error', '')}"
                )
        
        return True
    except Exception as e:
        logger.error(f"✗ Error verificando entidades: {e}", exc_info=True)
        return False


def main():
    """Ejecuta todas las pruebas de diagnóstico"""
    logger.info("="*60)
    logger.info("DIAGNÓSTICO DE INTEGRACIÓN BIDIRECCIONAL")
    logger.info("="*60)
    
    results = {}
    
    # Prueba 1: Configuración
    results['config'] = test_configuration()
    
    # Prueba 2: Token
    access_token = test_token_acquisition()
    results['token'] = access_token is not None
    
    # Prueba 3: Dynamics 365
    results['dynamics'] = test_dynamics_connection(access_token)
    
    # Prueba 4: e03800
    results['e03800'] = test_e03800_connection()
    
    # Prueba 5: interbus_365
    results['interbus_365'] = test_interbus_365_connection()
    
    # Prueba 6: Lógica de sincronización
    results['sync_logic'] = test_bidirectional_sync_logic(access_token)
    
    # Prueba 7: Todas las entidades
    results['all_entities'] = test_all_bidirectional_entities(access_token)
    
    # Resumen final
    logger.info("\n" + "="*60)
    logger.info("RESUMEN DE DIAGNÓSTICO")
    logger.info("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{test_name:<20} {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    logger.info(f"\nTotal: {passed_tests}/{total_tests} pruebas pasadas")
    
    if passed_tests == total_tests:
        logger.info("\n✓ TODAS LAS PRUEBAS PASARON")
        return 0
    else:
        logger.warning(f"\n⚠ {total_tests - passed_tests} PRUEBAS FALLARON")
        return 1


if __name__ == "__main__":
    sys.exit(main())
