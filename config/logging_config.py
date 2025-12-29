"""
Configuración de logging para la aplicación.
"""
import logging
import sys
from datetime import datetime


def setup_logging(log_to_file: bool = False, log_file: str = None):
    """
    Configura el sistema de logging.
    
    Args:
        log_to_file: Si se debe escribir a archivo
        log_file: Nombre del archivo de log
    """
    # Formato del log
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Si se solicita, agregar handler de archivo
    if log_to_file:
        if log_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = f'interbus_sync_{timestamp}.log'
        
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    # Configurar root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )
    
    return logging.getLogger(__name__)


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


