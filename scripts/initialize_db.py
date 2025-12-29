"""
Script para inicializar la base de datos MySQL.
Ejecuta el script SQL de creación de base de datos y tablas.
"""
import sys
import logging
import mysql.connector
from mysql.connector import Error
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_sql_file(cursor, sql_file_path: str):
    """
    Ejecuta un archivo SQL.
    
    Args:
        cursor: Cursor de MySQL
        sql_file_path: Ruta al archivo SQL
    """
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
            
        # Dividir el script en comandos
        commands = sql_script.split(';')
        
        for command in commands:
            command = command.strip()
            if command:
                cursor.execute(command)
        
        logger.info(f"Script SQL ejecutado correctamente: {sql_file_path}")
        
    except Error as e:
        logger.error(f"Error ejecutando script SQL: {e}")
        raise


def main():
    """Función principal."""
    logger.info("Inicializando base de datos...")
    
    try:
        # Conectar a MySQL (sin especificar base de datos)
        connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password
        )
        
        cursor = connection.cursor()
        
        # Ejecutar script SQL
        sql_file_path = 'database/create_database.sql'
        execute_sql_file(cursor, sql_file_path)
        
        connection.commit()
        logger.info("Base de datos inicializada correctamente")
        
    except Error as e:
        logger.error(f"Error inicializando base de datos: {e}")
        sys.exit(1)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()


if __name__ == "__main__":
    main()


