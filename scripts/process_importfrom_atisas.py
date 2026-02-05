import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.token_service import AzureADTokenService
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from infrastructure.employee_modifications_adapter import EmployeeModificationsAdapter
from utils.data_transformers import map_com_altas_to_importfrom_atisas
from utils.validators import validate_config


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        logger.error("Uso: python scripts/process_importfrom_atisas.py <com_altas_id>")
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

    if (com_altas_record.get('tipo') or '').upper() != 'M':
        logger.info(f"Registro {com_altas_id} no es modificacion (tipo != 'M').")
        return

    if (com_altas_record.get('estado') or '').upper() != 'L':
        logger.info(f"Registro {com_altas_id} no esta procesado (estado != 'L').")
        return

    dfo_status = adapter.get_dfo_com_altas_status(com_altas_id)
    if dfo_status:
        logger.info(f"Registro {com_altas_id} existe en dfo_com_altas. No se envia ImportfromATISAs.")
        return

    record = dict(com_altas_record)
    record['provincia'] = adapter.resolve_provincia_id(record.get('provincia'))
    record['nacionalidad'] = adapter.resolve_nacionalidad_cca3(record.get('nacionalidad'))

    payload = map_com_altas_to_importfrom_atisas(record)

    # Enviar solo campos con valor
    payload = {k: v for k, v in payload.items() if v not in (None, '')}

    if not payload:
        logger.error("No hay datos para enviar al endpoint ImportfromATISAs.")
        return

    token_service = AzureADTokenService()
    access_token = token_service.get_access_token()

    dynamics_api = DynamicsAPIAdapter()
    dynamics_api.create_entity_data(
        "ImportfromATISAs",
        access_token,
        payload
    )

    logger.info(f"ImportfromATISAs enviado OK para com_altas id: {com_altas_id}")


if __name__ == "__main__":
    main()
