from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from application.use_cases import SyncAllEntitiesUseCase, SyncDynamicsEntityUseCase
from application.bidirectional_sync_use_case import BidirectionalSyncUseCase
from application.employee_modifications_use_case import SyncEmployeeModificationsUseCase
from config.logging_config import setup_logging
from domain.constants import ENTITIES
from infrastructure.database_adapter import MySQLDatabaseAdapter
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from infrastructure.employee_modifications_adapter import EmployeeModificationsAdapter
from infrastructure.e03800_database_adapter import E03800DatabaseAdapter
from infrastructure.token_service import AzureADTokenService
from utils.data_transformers import (
    map_com_altas_to_employee_modifications,
    decode_etag_base64,
    normalize_etag,
    map_com_altas_to_importfrom_atisas
)
from utils.validators import validate_config, validate_entity_name


logger = setup_logging()
app = FastAPI(title="Interbus Integration API", version="1.0.0")


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


class SyncLimitRequest(BaseModel):
    limit: Optional[int] = None


class SyncTrabajadoresRequest(BaseModel):
    limit: Optional[int] = None


def _ensure_config() -> None:
    if not validate_config():
        raise HTTPException(status_code=500, detail="Configuración inválida (.env)")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/sync/all")
def sync_all() -> Dict[str, Any]:
    _ensure_config()
    token_service = AzureADTokenService()
    dynamics_api = DynamicsAPIAdapter()
    database_adapter = MySQLDatabaseAdapter()

    database_adapter.initialize_database()

    results: List[Dict[str, Any]] = []

    # 1) Bidireccional
    for entity in BIDIRECTIONAL_ENTITIES:
        if entity in ENTITIES:
            bidirectional_use_case = BidirectionalSyncUseCase(
                token_service,
                dynamics_api,
                database_adapter
            )
            results.append(bidirectional_use_case.execute(entity))

    # 2) Standard
    standard_entities = [e for e in ENTITIES if e not in BIDIRECTIONAL_ENTITIES]
    if standard_entities:
        sync_all_use_case = SyncAllEntitiesUseCase(
            token_service,
            dynamics_api,
            database_adapter
        )
        results.extend(sync_all_use_case.execute(standard_entities))

    return {"results": results}


@app.post("/sync/entity/{entity_name}")
def sync_entity(entity_name: str) -> Dict[str, Any]:
    _ensure_config()
    if not validate_entity_name(entity_name):
        raise HTTPException(status_code=400, detail=f"Entidad no válida: {entity_name}")

    token_service = AzureADTokenService()
    dynamics_api = DynamicsAPIAdapter()
    database_adapter = MySQLDatabaseAdapter()
    database_adapter.initialize_database()

    if entity_name in BIDIRECTIONAL_ENTITIES:
        use_case = BidirectionalSyncUseCase(token_service, dynamics_api, database_adapter)
        return use_case.execute(entity_name)

    use_case = SyncDynamicsEntityUseCase(token_service, dynamics_api, database_adapter)
    return use_case.execute(entity_name)


@app.post("/sync/employee-modifications")
def sync_employee_modifications(payload: SyncLimitRequest) -> Dict[str, Any]:
    _ensure_config()
    token_service = AzureADTokenService()
    access_token = token_service.get_access_token()

    dynamics_api = DynamicsAPIAdapter()
    employee_adapter = EmployeeModificationsAdapter()
    e03800_adapter = E03800DatabaseAdapter()

    use_case = SyncEmployeeModificationsUseCase(
        dynamics_api,
        employee_adapter,
        e03800_adapter
    )

    stats = use_case.sync(access_token, payload.limit)
    return stats


@app.post("/employee-modifications/process/{com_altas_id}")
def process_employee_modification(com_altas_id: int) -> Dict[str, Any]:
    _ensure_config()
    adapter = EmployeeModificationsAdapter()

    com_altas_record = adapter.get_com_altas_by_id(com_altas_id)
    if not com_altas_record:
        raise HTTPException(status_code=404, detail="com_altas no encontrado")

    dfo_status = adapter.get_dfo_com_altas_status(com_altas_id)
    if not dfo_status:
        raise HTTPException(status_code=404, detail="dfo_com_altas no encontrado")

    if int(dfo_status.get('procesado') or 0) == 1:
        return {"status": "skipped", "reason": "already_processed"}

    personnel_number = com_altas_record.get('nummat') or dfo_status.get('personnel_number')
    payload = map_com_altas_to_employee_modifications(
        com_altas_record,
        processed_value="Yes",
        personnel_number=personnel_number,
        only_processed=True
    )

    etag_base64 = dfo_status.get('etag')
    decoded_etag = decode_etag_base64(etag_base64)
    if not decoded_etag:
        raise HTTPException(status_code=400, detail="ETag inválido")

    filter_parts = []
    if personnel_number:
        escaped_personnel = str(personnel_number).replace("'", "''")
        filter_parts.append(f"PersonnelNumber eq '{escaped_personnel}'")
    filter_expression = " and ".join(filter_parts) if filter_parts else None

    token_service = AzureADTokenService()
    access_token = token_service.get_access_token()

    dynamics_api = DynamicsAPIAdapter()
    records = dynamics_api.get_entity_data(
        "EmployeeModifications",
        access_token,
        filter_expression=filter_expression,
        metadata="full"
    )
    record = next(
        (item for item in records if normalize_etag(item.get('@odata.etag', '')) == decoded_etag),
        None
    )

    if not record and personnel_number:
        records = dynamics_api.get_entity_data(
            "EmployeeModifications",
            access_token,
            metadata="full"
        )
        record = next(
            (item for item in records if normalize_etag(item.get('@odata.etag', '')) == decoded_etag),
            None
        )

    if not record:
        raise HTTPException(status_code=404, detail="Registro no encontrado en Dynamics")

    odata_id = record.get('@odata.id')
    data_area_id = record.get('dataAreaId') or 'itb'
    payload['TransitionReasonDescription'] = 'Procesado por integracion_interbus'

    if odata_id:
        dynamics_api.update_entity_data_by_url(
            odata_id,
            access_token,
            payload,
            if_match=decoded_etag
        )
    else:
        key_field_candidates = [
            'RecId',
            'EmployeeModificationsId',
            'EmployeeModificationId',
            'EQMEmployeeModificationsId'
        ]
        key_field = None
        key_value = None
        for candidate in key_field_candidates:
            if candidate in record:
                key_field = candidate
                key_value = record.get(candidate)
                break

        if key_field is None:
            raise HTTPException(status_code=400, detail="No se encontró campo clave")

        key_value_str = str(key_value).replace("'", "''")
        is_numeric = isinstance(key_value, int) or key_value_str.isdigit()
        if is_numeric:
            key_expr = f"{key_field}={key_value_str}"
        else:
            key_expr = f"{key_field}='{key_value_str}'"

        if key_field == 'RecId':
            entity_url = f"/data/EmployeeModifications({key_expr})?company={data_area_id}"
        else:
            entity_url = f"/data/EmployeeModifications(dataAreaId='{data_area_id}',{key_expr})?company={data_area_id}"

        dynamics_api.update_entity_data_by_url(
            entity_url,
            access_token,
            payload,
            if_match=decoded_etag
        )

    adapter.update_dfo_com_altas_processed(com_altas_id, 1)
    return {"status": "success", "id": com_altas_id}


@app.post("/importfrom-atisas/process/{com_altas_id}")
def process_importfrom_atisas(com_altas_id: int) -> Dict[str, Any]:
    _ensure_config()
    adapter = EmployeeModificationsAdapter()

    com_altas_record = adapter.get_com_altas_by_id(com_altas_id)
    if not com_altas_record:
        raise HTTPException(status_code=404, detail="com_altas no encontrado")

    if (com_altas_record.get('tipo') or '').upper() != 'M':
        return {"status": "skipped", "reason": "not_modification"}

    if (com_altas_record.get('estado') or '').upper() != 'L':
        return {"status": "skipped", "reason": "not_processed"}

    dfo_status = adapter.get_dfo_com_altas_status(com_altas_id)
    if dfo_status:
        return {"status": "skipped", "reason": "exists_in_dfo"}

    record = dict(com_altas_record)
    record['provincia'] = adapter.resolve_provincia_id(record.get('provincia'))
    record['nacionalidad'] = adapter.resolve_nacionalidad_cca3(record.get('nacionalidad'))

    payload = map_com_altas_to_importfrom_atisas(record)
    payload = {k: v for k, v in payload.items() if v not in (None, '')}

    if not payload:
        raise HTTPException(status_code=400, detail="No hay datos para enviar")

    token_service = AzureADTokenService()
    access_token = token_service.get_access_token()

    dynamics_api = DynamicsAPIAdapter()
    dynamics_api.create_entity_data(
        "ImportfromATISAs",
        access_token,
        payload
    )

    return {"status": "success", "id": com_altas_id}


@app.post("/trabajadores/sync-from-com-altas")
def sync_trabajadores(payload: SyncTrabajadoresRequest) -> Dict[str, Any]:
    _ensure_config()
    adapter = EmployeeModificationsAdapter()
    stats = adapter.sync_trabajadores_from_com_altas(payload.limit)
    return stats
