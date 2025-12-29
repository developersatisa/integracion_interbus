"""
Adaptador para operaciones de base de datos relacionadas con EmployeeModifications.
Maneja operaciones en dfo_com_altas (interbus_365) y com_altas (e03800).
"""
import mysql.connector
from mysql.connector import Error
from typing import Dict, Any, Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class EmployeeModificationsAdapter:
    """Adaptador para interactuar con las tablas relacionadas con EmployeeModifications."""
    
    def __init__(self):
        self._host = settings.db_host
        self._port = settings.db_port
        self._user = settings.db_user
        self._password = settings.db_password
        self._database_interbus = "interbus_365"
        self._database_e03800 = "e03800"
    
    def _get_connection_interbus_365(self):
        """Obtiene una conexión a la base de datos interbus_365."""
        try:
            connection = mysql.connector.connect(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                database=self._database_interbus,
                autocommit=False
            )
            return connection
        except Error as e:
            logger.error(f"Error conectando a MySQL interbus_365: {e}")
            raise
    
    def _get_connection_e03800(self):
        """Obtiene una conexión a la base de datos e03800."""
        try:
            connection = mysql.connector.connect(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                database=self._database_e03800,
                autocommit=False
            )
            return connection
        except Error as e:
            logger.error(f"Error conectando a MySQL e03800: {e}")
            raise
    
    def etag_exists(self, etag_encoded: str) -> bool:
        """
        Verifica si el ETag ya existe en dfo_com_altas.
        
        Args:
            etag_encoded: ETag codificado en base64
            
        Returns:
            True si existe, False si no existe
        """
        connection = None
        cursor = None
        
        try:
            connection = self._get_connection_interbus_365()
            cursor = connection.cursor()
            
            query = "SELECT COUNT(*) FROM dfo_com_altas WHERE etag = %s"
            cursor.execute(query, (etag_encoded,))
            count = cursor.fetchone()[0]
            
            return count > 0
            
        except Error as e:
            logger.error(f"Error verificando ETag: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_last_created_date_by_type(
        self, 
        codiemp: str, 
        nombre: str, 
        apellido1: str, 
        apellido2: str, 
        tipo: str,
        coditraba: Optional[str] = None
    ) -> Optional[str]:
        """
        Obtiene el último created_date de un tipo específico para un trabajador.
        Hace JOIN entre interbus_365.dfo_com_altas y e03800.com_altas.
        
        Args:
            codiemp: Código de empresa
            nombre: Nombre del trabajador
            apellido1: Primer apellido
            apellido2: Segundo apellido
            tipo: Tipo de registro ('A' o 'M')
            coditraba: Código de trabajador (solo para tipo 'M')
            
        Returns:
            String con la fecha más reciente, None si no hay registros
        """
        connection = None
        cursor = None
        
        try:
            # Usar conexión a interbus_365 (mismo servidor, puede hacer JOIN cruzado)
            connection = self._get_connection_interbus_365()
            cursor = connection.cursor()
            
            # Construir query con filtro de coditraba si es MODIFICACIÓN
            query = """
                SELECT MAX(dfo.created_date) as last_date
                FROM interbus_365.dfo_com_altas dfo
                JOIN e03800.com_altas ca ON dfo.id = ca.id
                WHERE ca.codiemp = %s
                  AND ca.nombre = %s
                  AND ca.apellido1 = %s
                  AND ca.apellido2 = %s
                  AND ca.tipo = %s
            """
            
            params = [codiemp, nombre, apellido1, apellido2, tipo]
            
            if tipo == 'M' and coditraba:
                query += " AND ca.coditraba = %s"
                params.append(coditraba)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            return result[0] if result and result[0] else None
            
        except Error as e:
            logger.error(f"Error obteniendo último created_date: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def insert_com_altas(self, data: Dict[str, Any]) -> int:
        """
        Inserta un registro en com_altas (base e03800).
        Retorna el id autoincremental generado.
        
        Args:
            data: Diccionario con los datos a insertar (solo campos no NULL)
            
        Returns:
            int: ID autoincremental generado
        """
        connection = None
        cursor = None
        
        try:
            connection = self._get_connection_e03800()
            cursor = connection.cursor()
            
            # Filtrar solo campos que no son None
            fields = [k for k, v in data.items() if v is not None]
            values = [data[k] for k in fields]
            
            if not fields:
                raise ValueError("No hay campos para insertar en com_altas")
            
            placeholders = ', '.join(['%s'] * len(fields))
            query = f"""
                INSERT INTO com_altas ({', '.join(fields)})
                VALUES ({placeholders})
            """
            
            cursor.execute(query, values)
            connection.commit()
            
            com_altas_id = cursor.lastrowid
            logger.info(f"Insertado registro en com_altas con id: {com_altas_id}")
            
            return com_altas_id
            
        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Error insertando en com_altas: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def insert_dfo_com_altas(
        self, 
        id: int, 
        etag: str, 
        personnel_number: Optional[str], 
        created_date: str
    ) -> bool:
        """
        Inserta un registro en dfo_com_altas (base interbus_365).
        
        Args:
            id: ID de com_altas (referencia)
            etag: ETag codificado en base64
            personnel_number: PersonnelNumber del endpoint (opcional)
            created_date: CreatedDate del endpoint
            
        Returns:
            True si se insertó correctamente
        """
        connection = None
        cursor = None
        
        try:
            connection = self._get_connection_interbus_365()
            cursor = connection.cursor()
            
            query = """
                INSERT INTO dfo_com_altas (id, etag, personnel_number, created_date)
                VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(query, (id, etag, personnel_number, created_date))
            connection.commit()
            
            logger.info(f"Insertado registro en dfo_com_altas con id: {id}")
            return True
            
        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Error insertando en dfo_com_altas: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

