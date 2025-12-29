"""
Script para verificar que el entorno esté configurado correctamente.
"""
import sys
import logging
from config.logging_config import setup_logging

logger = setup_logging()


def check_python_version():
    """Verifica la versión de Python."""
    logger.info("Verificando versión de Python...")
    
    if sys.version_info < (3, 8):
        logger.error(f"Python 3.8+ requerido. Versión actual: {sys.version}")
        return False
    
    logger.info(f"✓ Python versión: {sys.version.split()[0]}")
    return True


def check_dependencies():
    """Verifica que las dependencias estén instaladas."""
    logger.info("Verificando dependencias...")
    
    required_modules = [
        'pydantic_settings',
        'mysql.connector',
        'requests'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"✓ {module}")
        except ImportError:
            logger.error(f"✗ {module} no encontrado")
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"\nInstalar dependencias faltantes:")
        logger.error(f"pip install -r requirements.txt")
        return False
    
    return True


def check_configuration():
    """Verifica la configuración."""
    logger.info("Verificando configuración...")
    
    try:
        from utils.validators import validate_config
        
        if validate_config():
            logger.info("✓ Configuración válida")
            return True
        else:
            logger.error("✗ Configuración inválida")
            logger.error("Verifica el archivo .env")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error verificando configuración: {e}")
        return False


def check_database():
    """Verifica la conexión a la base de datos."""
    logger.info("Verificando conexión a base de datos...")
    
    try:
        from infrastructure.database_adapter import MySQLDatabaseAdapter
        
        database_adapter = MySQLDatabaseAdapter()
        
        # Intentar obtener conexión
        connection = database_adapter._get_connection()
        connection.close()
        
        logger.info("✓ Conexión a base de datos exitosa")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error conectando a base de datos: {e}")
        logger.error("Verifica las credenciales en .env")
        return False


def check_azure_credentials():
    """Verifica que las credenciales de Azure funcionen."""
    logger.info("Verificando credenciales de Azure AD...")
    
    try:
        from infrastructure.token_service import AzureADTokenService
        
        token_service = AzureADTokenService()
        token = token_service.get_access_token()
        
        logger.info("✓ Credenciales de Azure AD válidas")
        logger.info(f"✓ Token obtenido: {token[:50]}...")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error obteniendo token: {e}")
        logger.error("Verifica las credenciales de Azure AD en .env")
        return False


def main():
    """Función principal."""
    logger.info("="*60)
    logger.info("VERIFICACIÓN DEL ENTORNO")
    logger.info("="*60)
    
    checks = [
        ("Versión de Python", check_python_version),
        ("Dependencias", check_dependencies),
        ("Configuración", check_configuration),
        ("Base de Datos", check_database),
        ("Credenciales Azure AD", check_azure_credentials)
    ]
    
    results = []
    
    for name, check_func in checks:
        logger.info(f"\n{name}:")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Error en verificación: {e}")
            results.append((name, False))
    
    # Resumen
    logger.info("\n" + "="*60)
    logger.info("RESUMEN DE VERIFICACIÓN")
    logger.info("="*60)
    
    all_passed = True
    for name, result in results:
        status = "✓" if result else "✗"
        logger.info(f"{status} {name}")
        if not result:
            all_passed = False
    
    logger.info("="*60)
    
    if all_passed:
        logger.info("\n✓ Todas las verificaciones pasaron correctamente")
        logger.info("El entorno está listo para usar")
        logger.info("Ejecuta: python main.py")
        return 0
    else:
        logger.error("\n✗ Algunas verificaciones fallaron")
        logger.error("Corrige los errores antes de continuar")
        return 1


if __name__ == "__main__":
    sys.exit(main())


