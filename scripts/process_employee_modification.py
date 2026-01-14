import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.token_service import AzureADTokenService
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from infrastructure.employee_modifications_adapter import EmployeeModificationsAdapter
from utils.data_transformers import (
    map_com_altas_to_employee_modifications,
    decode_etag_base64,
    normalize_etag
)
from utils.validators import validate_config


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        logger.error("Uso: python scripts/process_employee_modification.py <com_altas_id>")
        return

    try:
        com_altas_id = int(sys.argv[1])
    except ValueError:
        logger.error(f"ID invalido: {sys.argv[1]}")
        return

    if not validate_config():
        return

    adapter = EmployeeModificationsAdapter()

    com_altas_record = adapter.get_com_altas_by_id(com_altas_id)
    if not com_altas_record:
        logger.error(f"No se encontro com_altas id: {com_altas_id}")
        return

    dfo_status = adapter.get_dfo_com_altas_status(com_altas_id)
    if not dfo_status:
        logger.error(f"No se encontro dfo_com_altas para id: {com_altas_id}")
        return

    if int(dfo_status.get('procesado') or 0) == 1:
        logger.info(f"Registro ya procesado en dfo_com_altas: {com_altas_id}")
        return

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
        logger.error(f"ETag inválido en dfo_com_altas para id: {com_altas_id}")
        return

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
        logger.error("No se encontró registro en Dynamics con el ETag indicado")
        return
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
            logger.error("No se encontró un campo clave para actualizar el registro")
            return

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
    logger.info(f"Procesado OK. dfo_com_altas actualizado para id: {com_altas_id}")


if __name__ == "__main__":
    main()
