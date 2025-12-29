"""
Caso de uso para sincronizar EmployeeModifications desde Dynamics 365.
Implementa la lógica de negocio para procesar altas y modificaciones.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from infrastructure.employee_modifications_adapter import EmployeeModificationsAdapter
from infrastructure.e03800_database_adapter import E03800DatabaseAdapter
from utils.data_transformers import (
    map_employee_to_com_altas,
    encode_etag_base64,
    normalize_null_or_empty,
    convert_datetime_iso_to_mysql
)

logger = logging.getLogger(__name__)


class SyncEmployeeModificationsUseCase:
    """Caso de uso para sincronizar EmployeeModifications."""
    
    def __init__(
        self,
        dynamics_api: DynamicsAPIAdapter,
        employee_adapter: EmployeeModificationsAdapter,
        e03800_adapter: E03800DatabaseAdapter
    ):
        self.dynamics_api = dynamics_api
        self.employee_adapter = employee_adapter
        self.e03800_adapter = e03800_adapter
    
    def _is_in_range(
        self, 
        created_date: datetime, 
        fechaalta: Optional[str], 
        fechabaja: Optional[str]
    ) -> bool:
        """
        Verifica si created_date está en el rango [fechaalta, fechabaja).
        
        Args:
            created_date: Fecha de creación del registro del endpoint
            fechaalta: Fecha de alta del trabajador (puede ser None)
            fechabaja: Fecha de baja del trabajador (puede ser None o vacío)
            
        Returns:
            True si está en rango, False si no
        """
        if not fechaalta:
            return False
        
        try:
            # Normalizar created_date a datetime si no lo es
            if isinstance(created_date, datetime):
                created_dt = created_date
            else:
                created_dt = datetime.fromisoformat(str(created_date).replace('Z', '+00:00'))
            
            # Convertir fechaalta (viene de MySQL, puede ser DATE o DATETIME)
            fechaalta_str = str(fechaalta)
            try:
                if 'T' in fechaalta_str or 'Z' in fechaalta_str or '+' in fechaalta_str:
                    fechaalta_dt = datetime.fromisoformat(fechaalta_str.replace('Z', '+00:00'))
                else:
                    # Es DATE o DATETIME de MySQL (YYYY-MM-DD o YYYY-MM-DD HH:MM:SS)
                    if len(fechaalta_str) == 10:  # Solo fecha
                        fechaalta_dt = datetime.strptime(fechaalta_str, '%Y-%m-%d')
                    else:
                        fechaalta_dt = datetime.strptime(fechaalta_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Último intento
                fechaalta_dt = datetime.fromisoformat(fechaalta_str.replace('Z', '+00:00'))
            
            # Normalizar ambos a naive para comparar
            if created_dt.tzinfo is not None:
                created_dt = created_dt.astimezone().replace(tzinfo=None)
            if fechaalta_dt.tzinfo is not None:
                fechaalta_dt = fechaalta_dt.astimezone().replace(tzinfo=None)
            
            # Si no hay fechabaja, el rango es [fechaalta, infinito)
            if not fechabaja or fechabaja == '':
                return created_dt >= fechaalta_dt
            
            # Si hay fechabaja, el rango es [fechaalta, fechabaja)
            fechabaja_str = str(fechabaja)
            try:
                if 'T' in fechabaja_str or 'Z' in fechabaja_str or '+' in fechabaja_str:
                    fechabaja_dt = datetime.fromisoformat(fechabaja_str.replace('Z', '+00:00'))
                else:
                    # Es DATE o DATETIME de MySQL
                    if len(fechabaja_str) == 10:  # Solo fecha
                        fechabaja_dt = datetime.strptime(fechabaja_str, '%Y-%m-%d')
                    else:
                        fechabaja_dt = datetime.strptime(fechabaja_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                fechabaja_dt = datetime.fromisoformat(fechabaja_str.replace('Z', '+00:00'))
            
            # Normalizar fechabaja a naive
            if fechabaja_dt.tzinfo is not None:
                fechabaja_dt = fechabaja_dt.astimezone().replace(tzinfo=None)
            
            return fechaalta_dt <= created_dt < fechabaja_dt
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error comparando fechas: {e}")
            return False
    
    def _identify_type(
        self, 
        record: Dict[str, Any], 
        created_date: datetime
    ) -> Dict[str, Any]:
        """
        Identifica si el registro es ALTA o MODIFICACIÓN.
        
        Args:
            record: Registro del endpoint EmployeeModifications
            created_date: CreatedDate del registro
            
        Returns:
            Dict con:
                - 'tipo': 'A' o 'M'
                - 'coditraba': Código de trabajador (0 para altas, código para modificaciones)
                - 'status': 'ok' o 'skipped'
                - 'reason': Razón si fue omitido
        """
        # Extraer campos de identificación
        codiemp = normalize_null_or_empty(record.get('CompanyIdATISA'))
        nombre = normalize_null_or_empty(record.get('FirstName'))
        apellido1 = normalize_null_or_empty(record.get('LastName1'))
        apellido2 = normalize_null_or_empty(record.get('LastName2'))
        
        if not all([codiemp, nombre, apellido1]):
            logger.warning("Faltan campos de identificación del trabajador")
            return {'status': 'skipped', 'reason': 'missing_fields'}
        
        # Buscar trabajador en tabla trabajadores
        trabajador_info = self.e03800_adapter.find_trabajador(
            codiemp, nombre, apellido1, apellido2 or ''
        )
        
        if trabajador_info is None:
            # CASO 1: Trabajador NO existe
            return {
                'tipo': 'A',
                'coditraba': '0',
                'status': 'ok'
            }
        
        # CASO 2: Trabajador SÍ existe
        has_active = trabajador_info.get('has_active', False)
        active_record = trabajador_info.get('active_record')
        
        if has_active and active_record:
            # CASO 2.A: Hay al menos un registro activo
            fechaalta = active_record.get('fechaalta')
            fechabaja = active_record.get('fechabaja')  # Será None o ''
            
            # Verificar rango
            if self._is_in_range(created_date, fechaalta, fechabaja):
                return {
                    'tipo': 'M',
                    'coditraba': str(active_record.get('coditraba', '0')),
                    'active_record': active_record,  # Pasar el registro activo para usar telefono
                    'status': 'ok'
                }
            else:
                # OMITIR - solicitud antigua, fuera del rango del trabajador activo
                return {
                    'status': 'skipped',
                    'reason': 'out_of_range',
                    'tipo': None,
                    'coditraba': None
                }
        else:
            # CASO 2.B: NO hay trabajador ACTIVO (todos los registros tienen fechabaja)
            ultima_fechabaja = self.e03800_adapter.get_last_fechabaja(
                codiemp, nombre, apellido1, apellido2 or ''
            )
            
            if ultima_fechabaja:
                # Convertir fechas para comparar
                try:
                    # Normalizar created_date
                    if isinstance(created_date, datetime):
                        created_dt = created_date
                    else:
                        created_dt = datetime.fromisoformat(str(created_date).replace('Z', '+00:00'))
                    
                    # Convertir ultima_fechabaja (viene de MySQL como DATE)
                    ultima_fechabaja_str = str(ultima_fechabaja)
                    try:
                        if 'T' in ultima_fechabaja_str or 'Z' in ultima_fechabaja_str or '+' in ultima_fechabaja_str:
                            ultima_fechabaja_dt = datetime.fromisoformat(ultima_fechabaja_str.replace('Z', '+00:00'))
                        else:
                            # Es DATE de MySQL (YYYY-MM-DD)
                            ultima_fechabaja_dt = datetime.strptime(ultima_fechabaja_str, '%Y-%m-%d')
                    except ValueError:
                        ultima_fechabaja_dt = datetime.fromisoformat(ultima_fechabaja_str.replace('Z', '+00:00'))
                    
                    # Normalizar ambos a naive para comparar
                    if created_dt.tzinfo is not None:
                        created_dt = created_dt.astimezone().replace(tzinfo=None)
                    if ultima_fechabaja_dt.tzinfo is not None:
                        ultima_fechabaja_dt = ultima_fechabaja_dt.astimezone().replace(tzinfo=None)
                    
                    if created_dt > ultima_fechabaja_dt:
                        return {
                            'tipo': 'A',
                            'coditraba': '0',
                            'status': 'ok'
                        }
                    else:
                        return {
                            'status': 'skipped',
                            'reason': 'old_request',
                            'tipo': None,
                            'coditraba': None
                        }
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Error comparando fechas de baja: {e}")
                    return {
                        'status': 'skipped',
                        'reason': 'date_error',
                        'tipo': None,
                        'coditraba': None
                    }
            else:
                # No hay fechabaja registrada, tratar como ALTA
                return {
                    'tipo': 'A',
                    'coditraba': '0',
                    'status': 'ok'
                }
    
    def _validate_chronological_order(
        self,
        created_date: datetime,
        codiemp: str,
        nombre: str,
        apellido1: str,
        apellido2: str,
        tipo: str,
        coditraba: Optional[str] = None
    ) -> bool:
        """
        Valida que el registro esté en orden cronológico según su tipo.
        
        Args:
            created_date: CreatedDate del registro actual
            codiemp: Código de empresa
            nombre: Nombre del trabajador
            apellido1: Primer apellido
            apellido2: Segundo apellido
            tipo: Tipo de registro ('A' o 'M')
            coditraba: Código de trabajador (solo para tipo 'M')
            
        Returns:
            True si está en orden cronológico, False si no
        """
        last_created_date = self.employee_adapter.get_last_created_date_by_type(
            codiemp, nombre, apellido1, apellido2 or '', tipo, coditraba
        )
        
        if last_created_date is None:
            # No hay registros previos de este tipo, está en orden
            return True
        
        try:
            # Normalizar created_date a datetime si no lo es
            if isinstance(created_date, datetime):
                created_dt = created_date
            else:
                created_dt = datetime.fromisoformat(str(created_date).replace('Z', '+00:00'))
            
            # Convertir last_created_date (viene de MySQL como DATETIME, puede ser naive o aware)
            last_created_str = str(last_created_date)
            
            # Intentar parsear como datetime aware primero
            try:
                if 'Z' in last_created_str or '+' in last_created_str or last_created_str.count('-') > 2:
                    # Tiene timezone info
                    last_dt = datetime.fromisoformat(last_created_str.replace('Z', '+00:00'))
                else:
                    # Es naive, crear como naive
                    last_dt = datetime.fromisoformat(last_created_str)
            except ValueError:
                # Si falla, intentar parsear como string MySQL (YYYY-MM-DD HH:MM:SS)
                try:
                    last_dt = datetime.strptime(last_created_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Último intento: solo fecha
                    last_dt = datetime.strptime(last_created_str, '%Y-%m-%d')
            
            # Normalizar ambos a naive para comparar (remover timezone si existe)
            if created_dt.tzinfo is not None:
                # Convertir a UTC y luego a naive
                created_dt = created_dt.astimezone().replace(tzinfo=None)
            
            if last_dt.tzinfo is not None:
                # Convertir a UTC y luego a naive
                last_dt = last_dt.astimezone().replace(tzinfo=None)
            
            return created_dt > last_dt
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error comparando fechas cronológicas: {e}")
            return False
    
    def process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un registro del endpoint EmployeeModifications.
        
        Args:
            record: Registro del endpoint
            
        Returns:
            Dict con el resultado del procesamiento
        """
        try:
            # PASO 1: Verificar ETag
            etag = record.get('@odata.etag', '')
            if not etag:
                return {'status': 'error', 'reason': 'missing_etag'}
            
            etag_encoded = encode_etag_base64(etag)
            if self.employee_adapter.etag_exists(etag_encoded):
                return {'status': 'skipped', 'reason': 'etag_exists'}
            
            # PASO 2: Identificar tipo (ALTA o MODIFICACIÓN)
            created_date_str = record.get('CreatedDate', '')
            if not created_date_str:
                return {'status': 'error', 'reason': 'missing_created_date'}
            
            created_date = datetime.fromisoformat(created_date_str.replace('Z', '+00:00'))
            type_info = self._identify_type(record, created_date)
            
            if type_info.get('status') != 'ok':
                return type_info
            
            tipo = type_info['tipo']
            coditraba = type_info['coditraba']
            active_record = type_info.get('active_record')  # Obtener active_record si existe (solo para MODIFICACIÓN)
            
            # PASO 3: Validación de orden cronológico
            codiemp = normalize_null_or_empty(record.get('CompanyIdATISA'))
            nombre = normalize_null_or_empty(record.get('FirstName'))
            apellido1 = normalize_null_or_empty(record.get('LastName1'))
            apellido2 = normalize_null_or_empty(record.get('LastName2'))
            
            is_chronological = self._validate_chronological_order(
                created_date, codiemp, nombre, apellido1, apellido2 or '', tipo,
                coditraba if tipo == 'M' else None
            )
            
            if not is_chronological:
                return {'status': 'skipped', 'reason': 'out_of_chronological_order'}
            
            # PASO 4: Mapear datos (pasar active_record para usar telefono de trabajadores si es MODIFICACIÓN)
            mapped_data = map_employee_to_com_altas(record, tipo, coditraba, active_record)
            
            # PASO 5: Crear registros
            # 5.1: Insertar en com_altas
            com_altas_id = self.employee_adapter.insert_com_altas(mapped_data)
            
            # 5.2: Insertar en dfo_com_altas
            personnel_number = normalize_null_or_empty(record.get('PersonnelNumber'))
            # Convertir created_date de ISO a formato MySQL DATETIME
            created_date_mysql = convert_datetime_iso_to_mysql(created_date_str)
            if not created_date_mysql:
                return {'status': 'error', 'reason': 'invalid_created_date_format'}
            
            self.employee_adapter.insert_dfo_com_altas(
                com_altas_id, etag_encoded, personnel_number, created_date_mysql
            )
            
            return {
                'status': 'success',
                'id': com_altas_id,
                'tipo': tipo,
                'etag': etag_encoded
            }
            
        except Exception as e:
            logger.error(f"Error procesando registro: {e}", exc_info=True)
            return {'status': 'error', 'reason': str(e)}
    
    def sync(self, access_token: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Sincroniza registros de EmployeeModifications.
        
        Args:
            access_token: Token de acceso de Azure AD
            limit: Límite de registros a procesar (None para todos)
            
        Returns:
            Dict con estadísticas del procesamiento
        """
        try:
            # Obtener datos del endpoint
            logger.info("Obteniendo datos de EmployeeModifications...")
            records = self.dynamics_api.get_entity_data("EmployeeModifications", access_token)
            
            if not records:
                logger.warning("No se obtuvieron registros del endpoint")
                return {
                    'total': 0,
                    'processed': 0,
                    'skipped': 0,
                    'errors': 0
                }
            
            # Limitar si se especifica
            if limit:
                records = records[:limit]
                logger.info(f"Procesando solo los primeros {limit} registros")
            
            # Procesar cada registro
            stats = {
                'total': len(records),
                'processed': 0,
                'skipped': 0,
                'errors': 0,
                'details': []
            }
            
            for idx, record in enumerate(records, 1):
                logger.info(f"Procesando registro {idx}/{len(records)}")
                result = self.process_record(record)
                
                if result.get('status') == 'success':
                    stats['processed'] += 1
                    logger.info(f"✓ Registro {idx} procesado exitosamente (id: {result.get('id')})")
                elif result.get('status') == 'skipped':
                    stats['skipped'] += 1
                    logger.info(f"⊘ Registro {idx} omitido: {result.get('reason')}")
                else:
                    stats['errors'] += 1
                    logger.error(f"✗ Error en registro {idx}: {result.get('reason')}")
                
                stats['details'].append({
                    'index': idx,
                    'result': result
                })
            
            logger.info(f"Procesamiento completado: {stats['processed']} procesados, {stats['skipped']} omitidos, {stats['errors']} errores")
            return stats
            
        except Exception as e:
            logger.error(f"Error en sincronización: {e}", exc_info=True)
            raise

