"""
Adaptador para la base de datos MySQL.
Implementa el puerto DatabaseAdapter.
"""
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class MySQLDatabaseAdapter:
    """Adaptador para interactuar con la base de datos MySQL."""
    
    def __init__(self):
        self._host = settings.db_host
        self._port = settings.db_port
        self._user = settings.db_user
        self._password = settings.db_password
        self._database = settings.db_name
    
    def _get_connection(self):
        """Obtiene una conexión a la base de datos."""
        try:
            connection = mysql.connector.connect(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                database=self._database,
                autocommit=False
            )
            return connection
        except Error as e:
            logger.error(f"Error conectando a MySQL: {e}")
            raise
    
    def _get_table_name(self, entity_name: str) -> str:
        """
        Convierte el nombre de entidad en nombre de tabla.
        
        Args:
            entity_name: Nombre de la entidad
            
        Returns:
            Nombre de la tabla
        """
        # Mapeo de entidades a tablas
        entity_to_table = {
            'CompanyATISAs': 'CompanyATISAs',
            'WorkerPlaces': 'WorkerPlaces',
            'ContributionAccountCodeCCs': 'ContributionAccountCodeCCs',
            'HolidaysAbsencesGroupATISAs': 'HolidaysAbsencesGroupATISAs',
            'VacationBalances': 'VacationBalances',
            'IncidentGroupATISAs': 'IncidentGroupATISAs',
            'AdvanceGroupATISAs': 'AdvanceGroupATISAs',
            'LibrariesGroupATISAs': 'LibrariesGroupATISAs',
            'LeaveGroupATISAs': 'LeaveGroupATISAs',
            'VacationCalenders': 'VacationCalenders',
            'HighsLowsChanges': 'HighsLowsChanges'
        }
        return entity_to_table.get(entity_name, entity_name)
    
    def save_entity_data(self, entity_name: str, data: List[Dict[Any, Any]]) -> int:
        """
        Guarda datos de una entidad en la base de datos.
        
        Args:
            entity_name: Nombre de la entidad
            data: Datos a guardar
            
        Returns:
            Número de registros guardados
        """
        if not data:
            logger.info(f"No hay datos para guardar en {entity_name}")
            return 0
        
        table_name = self._get_table_name(entity_name)
        connection = None
        cursor = None
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            records_saved = 0
            
            for record in data:
                # Convertir el registro a JSON para guardarlo
                import json
                json_data = json.dumps(record)
                
                # Insertar en la tabla (estructura genérica con id, entity_name, json_data)
                insert_query = """
                    INSERT INTO dynamic_entities (entity_name, json_data) 
                    VALUES (%s, %s)
                """
                
                cursor.execute(insert_query, (entity_name, json_data))
                records_saved += 1
            
            connection.commit()
            logger.info(f"Guardados {records_saved} registros en {table_name}")
            
            return records_saved
            
        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Error guardando datos en {entity_name}: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def clear_entity_data(self, entity_name: str) -> bool:
        """
        Limpia los datos de una entidad de la base de datos.
        
        Args:
            entity_name: Nombre de la entidad
            
        Returns:
            True si se limpió correctamente
        """
        connection = None
        cursor = None
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            # Eliminar registros de la entidad
            delete_query = "DELETE FROM dynamic_entities WHERE entity_name = %s"
            cursor.execute(delete_query, (entity_name,))
            
            connection.commit()
            logger.info(f"Limpieza de datos de {entity_name} completada")
            
            return True
            
        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Error limpiando datos de {entity_name}: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def initialize_database(self) -> bool:
        """
        Inicializa la base de datos creando las tablas necesarias.
        
        Returns:
            True si se inicializó correctamente
        """
        connection = None
        cursor = None
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            # Script para crear tabla genérica
            create_table_query = """
            CREATE TABLE IF NOT EXISTS dynamic_entities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                entity_name VARCHAR(100) NOT NULL,
                json_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_entity_name (entity_name),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            cursor.execute(create_table_query)
            connection.commit()
            
            logger.info("Base de datos inicializada correctamente")
            
            return True
            
        except Error as e:
            logger.error(f"Error inicializando base de datos: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


