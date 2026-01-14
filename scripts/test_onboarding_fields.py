import sys
import os
import logging
from datetime import datetime
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application.employee_modifications_use_case import SyncEmployeeModificationsUseCase
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from infrastructure.employee_modifications_adapter import EmployeeModificationsAdapter
from infrastructure.e03800_database_adapter import E03800DatabaseAdapter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_onboarding_mapping():
    logger.info("🚀 Iniciando prueba de mapeo de campos de Alta...")

    # 1. Mock Adapters
    dynamics_api = MagicMock(spec=DynamicsAPIAdapter)
    employee_adapter = MagicMock(spec=EmployeeModificationsAdapter)
    e03800_adapter = MagicMock(spec=E03800DatabaseAdapter)

    # 2. Setup Mock Data
    # Payload simulado de Dynamics con TODOS los campos nuevos
    test_payload = {
        '@odata.etag': 'W/"TestEtag123"',
        'CompanyIdATISA': '001',
        'FirstName': 'Juan',
        'LastName1': 'Perez',
        'LastName2': 'Gomez',
        'VATNum': '12345678Z',
        'Gender': 'Male',
        'NASS': '281234567890',
        'BirthDate': '1990-05-15T00:00:00Z',
        'Email': 'juan.perez@example.com',
        'Phone': '600123456',
        'ZipCode': '28001',
        'StartDate': '2025-01-01T00:00:00Z',
        'Salary': '25000.50',
        'BankAccount': 'ES0012345678901234567890',
        'HolidaysAbsencesGroupATISAId': '10',
        'LibrariesGroupATISAId': '20',
        'AdvanceGroupATISAId': '30',
        'CreatedDate': '2024-12-29T10:00:00Z',
        'PersonnelNumber': '000123',
        
        # Nuevos campos a probar
        'Street': 'C/ Mayor, 10, 2A',
        'City': 'Madrid',
        'County': 'Madrid',
        'JobPositionIdATISA': 'DEV01',
        'ContractTypeID': '100',
        'SeniorityDate': '2025-01-01T00:00:00Z',
        'EndDate': '2025-12-31T00:00:00Z',
        'Reasonforcontract': 'Sustitución'
    }

    # Configurar mocks
    dynamics_api.get_entity_data.return_value = [test_payload]
    
    # Simular que el ETag NO existe (es nuevo)
    employee_adapter.etag_exists.return_value = False
    
    # Simular que el trabajador NO existe (es Alta)
    e03800_adapter.find_trabajador.return_value = None
    
    # Simular inserción exitosa
    employee_adapter.insert_com_altas.return_value = 999
    employee_adapter.insert_dfo_com_altas.return_value = True
    
    # Simular que no hay fecha previa (validación cronológica OK)
    employee_adapter.get_last_created_date_by_type.return_value = None

    # 3. Ejecutar Use Case
    use_case = SyncEmployeeModificationsUseCase(dynamics_api, employee_adapter, e03800_adapter)
    
    # Llamamos directamente a process_record para ver el resultado detallado
    logger.info("🔄 Procesando registro simulado...")
    result = use_case.process_record(test_payload)

    # 4. Verificar Mapeo
    # Capturamos los argumentos con los que se llamó a insert_com_altas
    if employee_adapter.insert_com_altas.called:
        args, _ = employee_adapter.insert_com_altas.call_args
        mapped_data = args[0]
        
        logger.info("\n✅ Datos mapeados para inserción en com_altas:")
        for key, value in mapped_data.items():
            logger.info(f"  - {key}: {value}")
            
        # Validaciones específicas
        expected_fields = {
            'domicilio': 'C/ Mayor, 10, 2A',
            'localidad': 'Madrid',
            'provincia': 'Madrid',
            'nif': '12345678Z',
            'categoria_puesto': 'DEV01',
            'tipo_contrato': '100',
            'fecha_antig': '2025-01-01',
            'fechafincontrato': '2025-12-31',
            'motivo_contrato': 'Sustitución'
        }
        
        all_ok = True
        logger.info("\n🔍 Verificando campos nuevos:")
        for field, expected in expected_fields.items():
            actual = mapped_data.get(field)
            if str(actual) == str(expected):
                logger.info(f"  ✅ {field}: Correcto ({actual})")
            else:
                logger.error(f"  ❌ {field}: Incorrecto. Esperado: {expected}, Obtenido: {actual}")
                all_ok = False
        
        if all_ok:
            logger.info("\n🎉 PRUEBA EXITOSA: Todos los campos se mapearon correctamente.")
        else:
            logger.error("\n⚠️ PRUEBA FALLIDA: Algunos campos no coinciden.")
            
    else:
        logger.error("❌ insert_com_altas no fue llamado.")
        logger.error(f"Resultado del proceso: {result}")

if __name__ == "__main__":
    test_onboarding_mapping()
