import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.token_service import AzureADTokenService
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from utils.validators import validate_config


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 3:
        logger.error(
            "Uso: python scripts/update_worker_place.py <EQMWorkerPlaceID> <CompanyIdATISA> [Description]"
        )
        return

    worker_place_id = sys.argv[1].strip()
    company_id_atisa = sys.argv[2].strip()
    description = " ".join(sys.argv[3:]).strip() if len(sys.argv) > 3 else ""

    if not worker_place_id:
        logger.error("EQMWorkerPlaceID es obligatorio.")
        return

    if not validate_config():
        return

    payload = {}
    if company_id_atisa:
        payload["CompanyIdATISA"] = company_id_atisa
    if description:
        payload["Description"] = description

    if not payload:
        logger.error("No hay campos para actualizar.")
        return

    token_service = AzureADTokenService()
    access_token = token_service.get_access_token()

    dynamics_api = DynamicsAPIAdapter()
    dynamics_api.update_entity_data(
        entity_name="WorkerPlaces",
        access_token=access_token,
        item_id=worker_place_id,
        data=payload,
        key_field="EQMWorkerPlaceID"
    )

    logger.info(f"WorkerPlace actualizado OK: {worker_place_id}")


if __name__ == "__main__":
    main()
