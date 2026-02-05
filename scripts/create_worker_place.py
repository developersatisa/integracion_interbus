import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.token_service import AzureADTokenService
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from utils.validators import validate_config


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def _join_parts(*parts):
    cleaned = [str(p).strip() for p in parts if str(p).strip()]
    return ' '.join(cleaned)


def main():
    if len(sys.argv) < 7:
        logger.error(
            "Uso: python scripts/create_worker_place.py <codigop> <codigodom> <via> "
            "<calle> <cpostal> <municipio> [provincia]"
        )
        return

    codigop = sys.argv[1].strip()
    codigodom = sys.argv[2].strip()
    via = sys.argv[3]
    calle = sys.argv[4]
    cpostal = sys.argv[5]
    municipio = sys.argv[6]
    provincia = sys.argv[7] if len(sys.argv) > 7 else ""

    if not codigop or not codigodom:
        logger.error("codigop y codigodom son obligatorios.")
        return

    if not validate_config():
        return

    worker_place_id = f"{codigop}{codigodom}"
    description = _join_parts(via, calle, cpostal, municipio, provincia) or worker_place_id

    payload = {
        "dataAreaId": "itb",
        "EQMWorkerPlaceID": worker_place_id,
        "Description": description,
        "CompanyIdATISA": codigop
    }

    token_service = AzureADTokenService()
    access_token = token_service.get_access_token()

    dynamics_api = DynamicsAPIAdapter()
    dynamics_api.create_entity_data("WorkerPlaces", access_token, payload)

    logger.info(f"WorkerPlace creado OK: {worker_place_id}")


if __name__ == "__main__":
    main()
