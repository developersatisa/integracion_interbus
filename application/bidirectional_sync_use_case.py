"""
Caso de uso para sincronización bidireccional entre e03800 y Dynamics 365.
Compara datos y realiza las operaciones necesarias.
"""
from typing import Dict, Any, List, Optional
from domain.ports import TokenRepository, DynamicsAPIAdapter, DatabaseAdapter
from infrastructure.e03800_database_adapter import E03800DatabaseAdapter
import logging
import json

logger = logging.getLogger(__name__)


class BidirectionalSyncUseCase:
    """
    Caso de uso para sincronización bidireccional de HolidaysAbsencesGroupATISAs.
    Compara datos entre e03800 y Dynamics 365 y sincroniza.
    """
    
    def __init__(
        self,
        token_repository: TokenRepository,
        dynamics_api: DynamicsAPIAdapter,
        database_adapter: DatabaseAdapter
    ):
        self._token_repository = token_repository
        self._dynamics_api = dynamics_api
        self._database_adapter = database_adapter
        self._e03800_adapter = E03800DatabaseAdapter()
    
    def execute(self, entity_name: str = 'HolidaysAbsencesGroupATISAs') -> Dict[str, Any]:
        """
        Ejecuta la sincronización bidireccional.
        
        Args:
            entity_name: Nombre de la entidad (por defecto HolidaysAbsencesGroupATISAs)
            
        Returns:
            Diccionario con el resultado de la sincronización
        """
        try:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"SINCRONIZACIÓN BIDIRECCIONAL: {entity_name}")
            logger.info(f"{'=' * 60}")
            
            # 1. Obtener token
            access_token = self._token_repository.get_access_token()
            
            # 2. Obtener datos de e03800
            # CompanyATISAs -> tabla especial empresas
            # WorkerPlaces -> DBF contrcen.dbf
            # VacationCalenders -> tabla especial vac_calendarios (año actual)
            # Otras entidades -> tabla gruposervicios con id_servicios específico
            if entity_name == 'CompanyATISAs':
                e03800_data = self._e03800_adapter.get_empresas()
                logger.info(f"✓ e03800: {len(e03800_data)} registros (empresas)")
            elif entity_name == 'WorkerPlaces':
                e03800_data = self._e03800_adapter.get_worker_places()
                logger.info(f"✓ e03800: {len(e03800_data)} registros (contrcen.dbf FacilityCode)")
            elif entity_name == 'ContributionAccountCodeCCs':
                e03800_data = self._e03800_adapter.get_contribution_account_code_ccs()
                logger.info(f"✓ e03800: {len(e03800_data)} registros (ccc + contrcen.dbf)")
            elif entity_name == 'VacationBalances':
                e03800_data = self._e03800_adapter.get_vacation_balances()
                logger.info(f"✓ e03800: {len(e03800_data)} registros (convvacas)")
            elif entity_name == 'VacationCalenders':
                e03800_data = self._e03800_adapter.get_vacation_calendars_current_year()
                logger.info(f"✓ e03800: {len(e03800_data)} registros (vac_calendarios, año actual)")
            else:
                # HolidaysAbsencesGroupATISAs -> id_servicios = 30
                # IncidentGroupATISAs        -> id_servicios = 10
                # AdvanceGroupATISAs         -> id_servicios = 20
                # LibrariesGroupATISAs       -> id_servicios = 80
                # LeaveGroupATISAs           -> id_servicios = 100
                # HighsLowsChanges           -> id_servicios = 110
                if entity_name == 'HolidaysAbsencesGroupATISAs':
                    service_id = 30
                elif entity_name == 'IncidentGroupATISAs':
                    service_id = 10
                elif entity_name == 'AdvanceGroupATISAs':
                    service_id = 20
                elif entity_name == 'LibrariesGroupATISAs':
                    service_id = 80
                elif entity_name == 'LeaveGroupATISAs':
                    service_id = 100
                elif entity_name == 'HighsLowsChanges':
                    service_id = 110
                else:
                    service_id = 30
                e03800_data = self._e03800_adapter.get_gruposervicios_by_service(service_id)
                logger.info(f"✓ e03800: {len(e03800_data)} registros (id_servicios={service_id})")
            
            # 3. Obtener datos de Dynamics 365
            # Filtrar por dataAreaId='itb' solo para las entidades que lo soportan
            # ContributionAccountCodeCCs y VacationBalances no tienen dataAreaId
            if entity_name not in ['ContributionAccountCodeCCs', 'VacationBalances']:
                dynamics_data = self._dynamics_api.get_entity_data(entity_name, access_token, filter_expression="dataAreaId eq 'itb'")
            else:
                dynamics_data = self._dynamics_api.get_entity_data(entity_name, access_token)
            
            logger.info(f"✓ Dynamics 365: {len(dynamics_data)} registros")
            
            # 4. Comparar y determinar acciones
            sync_result = self._compare_and_sync(
                e03800_data,
                dynamics_data,
                access_token,
                entity_name
            )
            
            # 5. Obtener datos actualizados de Dynamics después de los cambios
            updated_dynamics_data = self._dynamics_api.get_entity_data(entity_name, access_token)
            
            # 6. Actualizar base de datos interbus_365 con los datos actualizados
            self._database_adapter.clear_entity_data(entity_name)
            records_saved = self._database_adapter.save_entity_data(entity_name, updated_dynamics_data)
            
            # Mostrar resumen
            logger.info(f"\n📊 Resumen de acciones:")
            logger.info(f"   ➕ Nuevos:              {len(sync_result['created'])}")
            logger.info(f"   🔄 Actualizados:        {len(sync_result['updated'])}")
            logger.info(f"   ❌ Eliminados:          {len(sync_result['deleted'])}")
            logger.info(f"   ✓ Sin cambios:          {len(sync_result['unchanged'])}")
            logger.info(f"   💾 Guardados en BD:     {records_saved} registros")
            
            return {
                "success": True,
                "entity": entity_name,
                "e03800_count": len(e03800_data),
                "dynamics_initial_count": len(dynamics_data),
                "dynamics_final_count": len(updated_dynamics_data),
                "records_saved": records_saved,
                "actions_taken": sync_result
            }
            
        except Exception as e:
            logger.error(f"Error en sincronización bidireccional: {e}", exc_info=True)
            return {
                "success": False,
                "entity": entity_name,
                "error": str(e)
            }
    
    def _compare_and_sync(
        self,
        e03800_data: List[Dict[str, Any]],
        dynamics_data: List[Dict[str, Any]],
        access_token: str,
        entity_name: str
    ) -> Dict[str, Any]:
        """
        Compara los datos y realiza las acciones necesarias.
        
        LÓGICA:
        1. Por cada registro de Dynamics, buscar su dataAreaId en e03800
        2. Comparar Description (Dynamics) con nombre (e03800)
        3. Decidir acción: ELIMINAR, ACTUALIZAR, CREAR o SIN CAMBIOS
        
        Args:
            e03800_data: Datos de e03800 (tabla gruposervicios)
            dynamics_data: Datos de Dynamics 365
            access_token: Token de acceso
            entity_name: Nombre de la entidad
            
        Returns:
            Resumen de acciones realizadas
        """
        actions_taken = {
            "created": [],
            "deleted": [],
            "updated": [],
            "unchanged": []
        }
        
        # Crear diccionario de e03800: id -> datos completos (incluyendo nombre)
        # Para la mayoría de entidades almacenará {'nombre': ...}, 
        # pero para ContributionAccountCodeCCs almacenará {'nombre', 'eqmccc', 'eqmworkerplaceid', ...}
        e03800_dict = {item['id']: item for item in e03800_data}
        
        # Para ContributionAccountCodeCCs, crear diccionario adicional por EQMCCC para manejar casos especiales
        e03800_by_eqmccc = {}
        if entity_name == 'ContributionAccountCodeCCs':
            for item in e03800_data:
                eqmccc = item.get('eqmccc')
                if eqmccc:
                    if eqmccc not in e03800_by_eqmccc:
                        e03800_by_eqmccc[eqmccc] = []
                    e03800_by_eqmccc[eqmccc].append(item)
        
        # 1. Iterar sobre cada registro de Dynamics y comparar
        seen_dynamics_ids = set()
        
        for dynamics_record in dynamics_data:
            data_area_id = self._extract_data_area_id_from_dynamics(dynamics_record, entity_name)
            dynamics_description = self._extract_description_from_dynamics(dynamics_record)
            
            if not data_area_id:
                continue
            
            # --- DETECCIÓN Y ELIMINACIÓN DE DUPLICADOS ---
            if data_area_id in seen_dynamics_ids:
                logger.warning(f"   ⚠️ DUPLICADO DETECTADO en Dynamics: {data_area_id}. Eliminando...")
                try:
                    # Determinar el campo clave para el borrado
                    if entity_name == 'HolidaysAbsencesGroupATISAs':
                        key_field = 'EQMHolidaysAbsencesGroupATISAId'
                    elif entity_name == 'IncidentGroupATISAs':
                        key_field = 'EQMIncidentGroupATISAId'
                    elif entity_name == 'AdvanceGroupATISAs':
                        key_field = 'EQMAdvanceGroupATISAId'
                    elif entity_name == 'LibrariesGroupATISAs':
                        key_field = 'EQMLibrariesGroupATISAId'
                    elif entity_name == 'LeaveGroupATISAs':
                        key_field = 'EQMLeaveGroupATISAId'
                    elif entity_name == 'HighsLowsChanges':
                        key_field = 'EQMHighsLowsChangesID'
                    elif entity_name == 'VacationCalenders':
                        key_field = 'EQMVacationCalenderId'
                    elif entity_name == 'CompanyATISAs':
                        key_field = 'EQMCompanyIdATISA'
                    elif entity_name == 'WorkerPlaces':
                        key_field = 'EQMWorkerPlaceID'
                    elif entity_name == 'ContributionAccountCodeCCs':
                        key_field = 'EQMCCC'
                    else:
                        key_field = 'EQMHolidaysAbsencesGroupATISAId'
                    
                    self._delete_from_dynamics(entity_name, dynamics_record, data_area_id, access_token, key_field)
                    if "duplicates_removed" not in actions_taken:
                        actions_taken["duplicates_removed"] = []
                    actions_taken["duplicates_removed"].append(data_area_id)
                    continue # Pasar al siguiente registro de Dynamics
                except Exception as e:
                    logger.error(f"   ✗ Error al eliminar duplicado: {e}")
                    # Continuar procesando aunque falle el borrado del duplicado
            
            seen_dynamics_ids.add(data_area_id)
            # ---------------------------------------------

            # Buscar en e03800
            found_in_e03800 = False
            e03800_item = None
            
            if data_area_id in e03800_dict:
                # Coincidencia exacta
                found_in_e03800 = True
                e03800_item = e03800_dict[data_area_id]
            elif entity_name == 'ContributionAccountCodeCCs':
                # Lógica especial para ContributionAccountCodeCCs
                eqmccc = str(dynamics_record.get('EQMCCC', ''))
                eqmworkerplaceid = str(dynamics_record.get('EQMWorkerPlaceID', ''))
                
                # Asumimos que todos los registros en Dynamics tienen EQMWorkerPlaceID completo
                # Si está vacío, es un error de datos - omitir el registro
                if not eqmworkerplaceid:
                    continue  # Omitir este registro
                elif eqmccc in e03800_by_eqmccc:
                    # Buscar coincidencia exacta
                    for item in e03800_by_eqmccc[eqmccc]:
                        if item['id'] == data_area_id:
                            found_in_e03800 = True
                            e03800_item = item
                            break
            
            if found_in_e03800:
                # Existe en e03800, comparar nombre
                e03800_nombre = e03800_item['nombre']
                
                if entity_name in ['ContributionAccountCodeCCs', 'VacationBalances']:
                    # Estas entidades no tienen campo Description o no soportan actualización parcial
                    # Si existe en e03800, considerarlo sin cambios
                    actions_taken["unchanged"].append(data_area_id)
                elif entity_name == 'CompanyATISAs':
                    # Para empresas, comparar nombre y CIF (VATNum)
                    e03800_cif = str(e03800_item.get('cif') or '').strip()
                    dynamics_cif = str(dynamics_record.get('VATNum') or '').strip()
                    e03800_quotation = str(e03800_item.get('quotation_account') or '').strip()
                    dynamics_quotation = str(dynamics_record.get('QuotationAccount') or '').strip()
                    
                    if (
                        dynamics_description == e03800_nombre
                        and dynamics_cif == e03800_cif
                        and dynamics_quotation == e03800_quotation
                    ):
                        # Sin cambios
                        actions_taken["unchanged"].append(data_area_id)
                    else:
                        # Nombre o CIF diferente, ACTUALIZAR
                        try:
                            key_field = 'EQMCompanyIdATISA'
                            # Pasar el item completo para que _update_in_dynamics pueda extraer el CIF
                            self._update_in_dynamics(entity_name, dynamics_record, data_area_id, e03800_nombre, access_token, key_field, e03800_item)
                            actions_taken["updated"].append(data_area_id)
                        except Exception as e:
                            logger.error(f"   ✗ Error al actualizar {data_area_id}: {e}")
                elif dynamics_description == e03800_nombre:
                    # Sin cambios
                    actions_taken["unchanged"].append(data_area_id)
                else:
                    # Descripción diferente, ACTUALIZAR
                    try:
                        if entity_name == 'HolidaysAbsencesGroupATISAs':
                            key_field = 'EQMHolidaysAbsencesGroupATISAId'
                        elif entity_name == 'IncidentGroupATISAs':
                            key_field = 'EQMIncidentGroupATISAId'
                        elif entity_name == 'AdvanceGroupATISAs':
                            key_field = 'EQMAdvanceGroupATISAId'
                        elif entity_name == 'LibrariesGroupATISAs':
                            key_field = 'EQMLibrariesGroupATISAId'
                        elif entity_name == 'LeaveGroupATISAs':
                            key_field = 'EQMLeaveGroupATISAId'
                        elif entity_name == 'HighsLowsChanges':
                            key_field = 'EQMHighsLowsChangesID'
                        elif entity_name == 'VacationCalenders':
                            key_field = 'EQMVacationCalenderId'
                        elif entity_name == 'WorkerPlaces':
                            key_field = 'EQMWorkerPlaceID'
                        elif entity_name == 'VacationBalances':
                            key_field = 'EQMVacationBalanceId'
                        else:
                            key_field = 'EQMHolidaysAbsencesGroupATISAId'
                        self._update_in_dynamics(entity_name, dynamics_record, data_area_id, e03800_nombre, access_token, key_field)
                        actions_taken["updated"].append(data_area_id)
                    except Exception as e:
                        logger.error(f"   ✗ Error al actualizar {data_area_id}: {e}")
            else:
                # No existe en e03800, ELIMINAR de Dynamics
                try:
                    if entity_name == 'HolidaysAbsencesGroupATISAs':
                        key_field = 'EQMHolidaysAbsencesGroupATISAId'
                    elif entity_name == 'IncidentGroupATISAs':
                        key_field = 'EQMIncidentGroupATISAId'
                    elif entity_name == 'AdvanceGroupATISAs':
                        key_field = 'EQMAdvanceGroupATISAId'
                    elif entity_name == 'LibrariesGroupATISAs':
                        key_field = 'EQMLibrariesGroupATISAId'
                    elif entity_name == 'LeaveGroupATISAs':
                        key_field = 'EQMLeaveGroupATISAId'
                    elif entity_name == 'HighsLowsChanges':
                        key_field = 'EQMHighsLowsChangesID'
                    elif entity_name == 'VacationCalenders':
                        key_field = 'EQMVacationCalenderId'
                    elif entity_name == 'CompanyATISAs':
                        key_field = 'EQMCompanyIdATISA'
                    elif entity_name == 'WorkerPlaces':
                        key_field = 'EQMWorkerPlaceID'
                    elif entity_name == 'VacationBalances':
                        key_field = 'EQMVacationBalanceId'
                    elif entity_name == 'ContributionAccountCodeCCs':
                        # ContributionAccountCodeCCs usa claves compuestas, usar la combinación
                        key_field = 'EQMCCC'  # Usar EQMCCC como campo de referencia
                    else:
                        key_field = 'EQMHolidaysAbsencesGroupATISAId'
                    
                    self._delete_from_dynamics(entity_name, dynamics_record, data_area_id, access_token, key_field)
                    actions_taken["deleted"].append(data_area_id)
                except Exception as e:
                    # Solo logear errores reales, no errores esperados
                    error_str = str(e)
                    if "No route data was found" not in error_str and "No HTTP resource was found" not in error_str:
                        logger.error(f"   ✗ Error al eliminar: {e}")
                    # No hacer raise para continuar con otros registros
        
        # 2. Buscar registros en e03800 que no existen en Dynamics → CREAR
        dynamics_ids = set([self._extract_data_area_id_from_dynamics(record, entity_name) for record in dynamics_data])
        dynamics_ids = {id for id in dynamics_ids if id}  # Filtrar None
        
        # Log para depuración
        if entity_name == 'VacationCalenders':
            logger.info(f"\n🔍 DEBUG VacationCalenders:")
            logger.info(f"   IDs en e03800 (año actual): {list(e03800_dict.keys())}")
            logger.info(f"   IDs en Dynamics (todos los años): {dynamics_ids}")
            logger.info(f"   IDs a crear: {[id for id in e03800_dict.keys() if id not in dynamics_ids]}")
        
        for item_id, e03800_item in e03800_dict.items():
            if item_id not in dynamics_ids:
                # No existe en Dynamics, CREAR
                item_nombre = e03800_item['nombre']
                if entity_name == 'HolidaysAbsencesGroupATISAs':
                    data_to_create = {
                        "dataAreaId": "itb",
                        "EQMHolidaysAbsencesGroupATISAId": item_id,
                        "Description": item_nombre
                    }
                elif entity_name == 'IncidentGroupATISAs':
                    data_to_create = {
                        "dataAreaId": "itb",
                        "EQMIncidentGroupATISAId": item_id,
                        "Description": item_nombre
                    }
                elif entity_name == 'AdvanceGroupATISAs':
                    data_to_create = {
                        "dataAreaId": "itb",
                        "EQMAdvanceGroupATISAId": item_id,
                        "Description": item_nombre
                    }
                elif entity_name == 'LibrariesGroupATISAs':
                    data_to_create = {
                        "dataAreaId": "itb",
                        "EQMLibrariesGroupATISAId": item_id,
                        "Description": item_nombre
                    }
                elif entity_name == 'LeaveGroupATISAs':
                    data_to_create = {
                        "dataAreaId": "itb",
                        "EQMLeaveGroupATISAId": item_id,
                        "Description": item_nombre
                    }
                elif entity_name == 'HighsLowsChanges':
                    data_to_create = {
                        "dataAreaId": "itb",
                        "EQMHighsLowsChangesID": item_id,
                        "Description": item_nombre
                    }
                elif entity_name == 'VacationCalenders':
                    data_to_create = {
                        "dataAreaId": "itb",
                        "EQMVacationCalenderId": item_id,
                        "Description": item_nombre
                    }
                elif entity_name == 'CompanyATISAs':
                    data_to_create = {
                        "dataAreaId": "itb",
                        "EQMCompanyIdATISA": item_id,
                        "Description": item_nombre,
                        "VATNum": str(e03800_item.get('cif') or '').strip(),
                        "QuotationAccount": str(e03800_item.get('quotation_account') or '').strip()
                    }
                elif entity_name == 'WorkerPlaces':
                    data_to_create = {
                        "dataAreaId": "itb",
                        "EQMWorkerPlaceID": item_id,
                        "Description": item_nombre,
                        "CompanyIdAtisa": str(e03800_item.get('codiemp') or '').strip()
                    }
                elif entity_name == 'ContributionAccountCodeCCs':
                    # ContributionAccountCodeCCs: requiere EQMCCC, EQMWorkerPlaceID y VATNum (CIF)
                    data_to_create = {
                        "EQMCCC": e03800_item.get('eqmccc', ''),
                        "EQMWorkerPlaceID": e03800_item.get('eqmworkerplaceid', ''),
                        "VATNum": e03800_item.get('cif', '')
                    }
                elif entity_name == 'VacationBalances':
                    # VacationBalances: requiere dataAreaId para la ruta, pero no tiene Description
                    data_to_create = {
                        "dataAreaId": "itb",
                        "EQMVacationBalanceId": item_id
                    }
                else:
                    data_to_create = {
                        "dataAreaId": "itb",
                        "EQMHolidaysAbsencesGroupATISAId": item_id,
                        "Description": item_nombre
                    }
                
                try:
                    logger.debug(f"   Intentando crear registro ID: {item_id}")
                    logger.debug(f"   Datos a enviar: {data_to_create}")
                    self._dynamics_api.create_entity_data(entity_name, access_token, data_to_create)
                    logger.info(f"   ✓ Creado registro ID: {item_id}")
                    actions_taken["created"].append(item_id)
                except Exception as e:
                    error_message = str(e)
                    # Si el registro ya existe, registrarlo pero continuar
                    if "already exists" in error_message or "ya existe" in error_message:
                        logger.warning(f"   ⚠ Registro ya existe en Dynamics: {item_id}")
                        actions_taken["unchanged"].append(item_id)
                    else:
                        logger.error(f"   ✗ Error al crear registro ID {item_id}: {e}")
                        logger.error(f"   Datos que causaron el error: {data_to_create}")
                        # Agregar a una lista de errores para tracking
                        if "errors" not in actions_taken:
                            actions_taken["errors"] = []
                        actions_taken["errors"].append({"id": item_id, "error": error_message})
                        # No hacer raise para continuar con otros registros
        
        return actions_taken
    
    def _extract_data_area_id_from_dynamics(self, dynamics_item: Dict[str, Any], entity_name: str) -> str:
        """
        Extrae el identificador de un registro de Dynamics 365.
        Usa el campo específico según la entidad.
        Este será usado para buscar en e03800 (campo id).
        
        Args:
            dynamics_item: Registro de Dynamics
            entity_name: Nombre de la entidad
            
        Returns:
            ID del registro o None
        """
        # Determinar campo específico según la entidad
        if entity_name == 'HolidaysAbsencesGroupATISAs':
            primary_field = 'EQMHolidaysAbsencesGroupATISAId'
        elif entity_name == 'IncidentGroupATISAs':
            primary_field = 'EQMIncidentGroupATISAId'
        elif entity_name == 'AdvanceGroupATISAs':
            primary_field = 'EQMAdvanceGroupATISAId'
        elif entity_name == 'LibrariesGroupATISAs':
            primary_field = 'EQMLibrariesGroupATISAId'
        elif entity_name == 'LeaveGroupATISAs':
            primary_field = 'EQMLeaveGroupATISAId'
        elif entity_name == 'HighsLowsChanges':
            primary_field = 'EQMHighsLowsChangesID'
        elif entity_name == 'VacationCalenders':
            primary_field = 'EQMVacationCalenderId'
        elif entity_name == 'CompanyATISAs':
            primary_field = 'EQMCompanyIdATISA'
        elif entity_name == 'WorkerPlaces':
            primary_field = 'EQMWorkerPlaceID'
        elif entity_name == 'ContributionAccountCodeCCs':
            # ContributionAccountCodeCCs usa combinación de EQMCCC + EQMWorkerPlaceID
            eqmccc = str(dynamics_item.get('EQMCCC', ''))
            eqmworkerplaceid = str(dynamics_item.get('EQMWorkerPlaceID', ''))
            
            if eqmccc and eqmworkerplaceid:
                # Solo procesar registros con EQMWorkerPlaceID completo
                combined_id = f"{eqmccc}_{eqmworkerplaceid}"
                return combined_id
            else:
                # Si falta EQMWorkerPlaceID, omitir el registro (error de datos)
                return None
        elif entity_name == 'VacationBalances':
            # VacationBalances usa identificador EQMVacationBalanceId
            if 'EQMVacationBalanceId' in dynamics_item:
                return str(dynamics_item['EQMVacationBalanceId'])
            return None
        else:
            primary_field = 'EQMHolidaysAbsencesGroupATISAId'
        
        if primary_field in dynamics_item:
            return str(dynamics_item[primary_field])
        
        # Fallback: intentar otros campos posibles
        fallback_fields = ['HolidaysAbsencesGroupId', 'IncidentGroupId', 'groupId', 'dataAreaId']
        
        for field in fallback_fields:
            if field in dynamics_item:
                return str(dynamics_item[field])
        
        # Si no encuentra ningún campo conocido, buscar cualquier campo con ID
        for key, value in dynamics_item.items():
            if 'id' in key.lower() and key != 'RecId':
                return str(value)
        
        return None
    
    def _extract_description_from_dynamics(self, dynamics_item: Dict[str, Any]) -> str:
        """
        Extrae la descripción de un registro de Dynamics 365.
        
        Args:
            dynamics_item: Registro de Dynamics
            
        Returns:
            Descripción o cadena vacía
        """
        possible_fields = ['Description', 'description']
        
        for field in possible_fields:
            if field in dynamics_item:
                return str(dynamics_item[field])
        
        return ""
    
    def _prepare_create_data(self, e03800_item: Dict[str, Any], item_id: str) -> Dict[str, Any]:
        """
        Prepara los datos para crear en Dynamics 365.
        
        Args:
            e03800_item: Item de e03800 (dict con 'nombre')
            item_id: ID del item para usar como EQMHolidaysAbsencesGroupATISAId
            
        Returns:
            Datos formateados para Dynamics
        """
        return {
            "dataAreaId": "itb",
            "EQMHolidaysAbsencesGroupATISAId": item_id,
            "Description": e03800_item['nombre']
        }
    
    def _update_in_dynamics(
        self, 
        entity_name: str, 
        item: Dict[str, Any], 
        item_id: str, 
        new_description: str, 
        access_token: str,
        key_field: str,
        e03800_item: Optional[Dict[str, Any]] = None
    ):
        """
        Actualiza un registro en Dynamics 365.
        
        Args:
            entity_name: Nombre de la entidad
            item: Item a actualizar
            item_id: ID del registro
            new_description: Nueva descripción
            access_token: Token de acceso
        """
        # Actualizar la descripción en Dynamics 365
        update_data = {"Description": new_description}
        
        # Si es CompanyATISAs, incluir también el CIF (VATNum)
        if entity_name == 'CompanyATISAs' and e03800_item:
            update_data["VATNum"] = str(e03800_item.get('cif') or '').strip()
            update_data["QuotationAccount"] = str(e03800_item.get('quotation_account') or '').strip()
        
        self._dynamics_api.update_entity_data(
            entity_name=entity_name,
            access_token=access_token,
            item_id=item_id,
            data=update_data,
            key_field=key_field
        )
    
    def _delete_from_dynamics(
        self, 
        entity_name: str, 
        item: Dict[str, Any], 
        item_id: str, 
        access_token: str,
        key_field: str
    ):
        """
        Elimina un registro de Dynamics 365.
        
        Args:
            entity_name: Nombre de la entidad
            item: Item a eliminar
            item_id: ID del registro
            access_token: Token de acceso
        """
        # Usar el método del adaptador de Dynamics API
        self._dynamics_api.delete_entity_data(entity_name, access_token, item_id, key_field=key_field)

