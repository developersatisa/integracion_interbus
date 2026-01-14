import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.employee_modifications_adapter import EmployeeModificationsAdapter


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Límite inválido: {sys.argv[1]}. Procesando todos los registros.")

    adapter = EmployeeModificationsAdapter()
    stats = adapter.sync_trabajadores_from_com_altas(limit)

    logger.info("Sincronización completada:")
    logger.info(f"  Total: {stats['total']}")
    logger.info(f"  Creados: {stats['created']}")
    logger.info(f"  Omitidos: {stats['skipped']}")
    logger.info(f"  Errores: {stats['errors']}")


if __name__ == "__main__":
    main()
