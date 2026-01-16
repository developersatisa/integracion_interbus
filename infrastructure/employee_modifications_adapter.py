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
        self._database_acceso = "acceso"
        self._trabajadores_nif_column = None
        self._dfo_com_altas_processed_column = None
        self._provincias_integracion_db = None
        self._puestos_tables = {"lista_puestos", "lista_subpuestos"}

    def _truncate_str(self, value: Any, max_len: int) -> Optional[str]:
        """
        Trunca strings para ajustarse a los limites de columnas.
        """
        if value is None:
            return None
        value_str = str(value)
        if len(value_str) <= max_len:
            return value_str
        return value_str[:max_len]
    
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

    def _get_connection_acceso(self):
        """Obtiene una conexión a la base de datos acceso."""
        try:
            connection = mysql.connector.connect(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                database=self._database_acceso,
                autocommit=False
            )
            return connection
        except Error as e:
            logger.error(f"Error conectando a MySQL acceso: {e}")
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

    def get_com_altas_by_id(self, com_altas_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un registro de com_altas por ID.
        """
        connection = None
        cursor = None

        try:
            connection = self._get_connection_e03800()
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    id,
                    codiemp,
                    nombre,
                    apellido1,
                    apellido2,
                    sexo,
                    naf,
                    fechanacimiento,
                    email,
                    telefono,
                    cpostal,
                    fechaalta,
                    salario,
                    ccc,
                    nummat,
                    grupo_vacaciones,
                    grupo_biblioteca,
                    grupo_anticipos,
                    domicilio,
                    localidad,
                    provincia,
                    categoria_puesto,
                    tipo_contrato,
                    fecha_antig,
                    fechafincontrato,
                    motivo_contrato,
                    nif
                FROM com_altas
                WHERE id = %s
            """
            cursor.execute(query, (com_altas_id,))
            return cursor.fetchone()

        except Error as e:
            logger.error(f"Error obteniendo com_altas por id {com_altas_id}: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def _resolve_dfo_com_altas_processed_column(self, cursor) -> str:
        """
        Resuelve el nombre de columna de procesado en dfo_com_altas.
        Prioriza 'procesado' y cae a 'processed' si existe.
        """
        if self._dfo_com_altas_processed_column:
            return self._dfo_com_altas_processed_column

        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = 'dfo_com_altas'
              AND column_name IN ('procesado', 'processed')
            """,
            (self._database_interbus,)
        )
        columns = set()
        for row in cursor.fetchall():
            if isinstance(row, dict):
                columns.add(row.get('COLUMN_NAME'))
            else:
                columns.add(row[0])

        if 'procesado' in columns:
            self._dfo_com_altas_processed_column = 'procesado'
        elif 'processed' in columns:
            self._dfo_com_altas_processed_column = 'processed'
        else:
            self._dfo_com_altas_processed_column = 'procesado'

        return self._dfo_com_altas_processed_column

    def _resolve_provincias_integracion_db(self) -> str:
        """
        Detecta en qué base de datos existe provincias_integracion.
        """
        if self._provincias_integracion_db is not None:
            return self._provincias_integracion_db

        candidates = [
            (self._database_e03800, self._get_connection_e03800),
            (self._database_interbus, self._get_connection_interbus_365)
        ]

        for db_name, connector in candidates:
            connection = None
            cursor = None
            try:
                connection = connector()
                cursor = connection.cursor()
                cursor.execute(
                    """
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = %s
                      AND table_name = 'provincias_integracion'
                    LIMIT 1
                    """,
                    (db_name,)
                )
                if cursor.fetchone():
                    self._provincias_integracion_db = db_name
                    return self._provincias_integracion_db
            except Error as e:
                logger.warning(f"No se pudo verificar provincias_integracion en {db_name}: {e}")
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    connection.close()

        self._provincias_integracion_db = ''
        return self._provincias_integracion_db

    def resolve_provincia_descripcion(self, provincia_value: Optional[Any]) -> Optional[str]:
        """
        Resuelve provincia por ID usando provincias_integracion.
        """
        if provincia_value is None:
            return None

        value_str = str(provincia_value).strip()
        if not value_str:
            return None

        if not value_str.isdigit():
            return value_str

        db_name = self._resolve_provincias_integracion_db()
        if not db_name:
            return value_str

        connection = None
        cursor = None
        try:
            if db_name == self._database_e03800:
                connection = self._get_connection_e03800()
            else:
                connection = self._get_connection_interbus_365()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT descripcion FROM provincias_integracion WHERE id = %s LIMIT 1",
                (int(value_str),)
            )
            row = cursor.fetchone()
            if row:
                return row[0]
        except Error as e:
            logger.warning(f"Error resolviendo provincia {value_str}: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return value_str

    def resolve_nacionalidad_codigo(self, nacionalidad_value: Optional[Any]) -> Optional[Any]:
        """
        Resuelve nacionalidad usando acceso.paises (pais -> codpais).
        """
        if nacionalidad_value is None:
            return None

        value_str = str(nacionalidad_value).strip()
        if not value_str:
            return None

        connection = None
        cursor = None
        try:
            connection = self._get_connection_acceso()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT codpais FROM paises WHERE cca3 = %s LIMIT 1",
                (value_str,)
            )
            row = cursor.fetchone()
            if row:
                return row[0]
        except Error as e:
            logger.warning(f"Error resolviendo nacionalidad {value_str}: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return value_str

    def _fetch_puesto_catalog_entry(
        self,
        codiemp: Optional[str],
        search_value: Optional[str],
        table_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Busca en lista_puestos/lista_subpuestos por codiemp y concepto LIKE.
        """
        if table_name not in self._puestos_tables:
            raise ValueError(f"Tabla no soportada: {table_name}")

        if not codiemp or not search_value:
            return None

        value_str = str(search_value).strip()
        if not value_str:
            return None

        connection = None
        cursor = None
        try:
            connection = self._get_connection_e03800()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                f"""
                SELECT codpuesto, concepto
                FROM {table_name}
                WHERE codiemp = %s
                  AND concepto LIKE %s
                ORDER BY codpuesto
                LIMIT 1
                """,
                (codiemp, f"%{value_str}%")
            )
            return cursor.fetchone()
        except Error as e:
            logger.warning(f"Error buscando {table_name} para {codiemp}: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return None

    def resolve_puesto_codpuesto(
        self,
        codiemp: Optional[str],
        search_value: Optional[str],
        table_name: str
    ) -> Optional[str]:
        """
        Resuelve codpuesto a partir de un texto de concepto.
        """
        entry = self._fetch_puesto_catalog_entry(codiemp, search_value, table_name)
        if entry:
            return entry.get('codpuesto')
        return None

    def resolve_puesto_concepto(
        self,
        codiemp: Optional[str],
        codpuesto: Optional[Any],
        table_name: str
    ) -> Optional[str]:
        """
        Resuelve concepto a partir de codpuesto.
        """
        if table_name not in self._puestos_tables:
            raise ValueError(f"Tabla no soportada: {table_name}")

        if not codiemp or codpuesto is None:
            return None

        codpuesto_str = str(codpuesto).strip()
        if not codpuesto_str:
            return None

        connection = None
        cursor = None
        try:
            connection = self._get_connection_e03800()
            cursor = connection.cursor()
            cursor.execute(
                f"""
                SELECT concepto
                FROM {table_name}
                WHERE codiemp = %s
                  AND codpuesto = %s
                LIMIT 1
                """,
                (codiemp, codpuesto_str)
            )
            row = cursor.fetchone()
            if row:
                return row[0]
        except Error as e:
            logger.warning(f"Error resolviendo concepto {table_name} {codiemp}: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return None

    def extract_codpuesto(self, puesto_value: Optional[Any]) -> Optional[str]:
        """
        Extrae codpuesto desde un valor "codiemp-codpuesto" o directo.
        """
        if puesto_value is None:
            return None
        value_str = str(puesto_value).strip()
        if not value_str:
            return None
        if '-' in value_str:
            _, codpuesto = value_str.split('-', 1)
            return codpuesto.strip() or None
        return value_str

    def get_dfo_com_altas_status(self, com_altas_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de dfo_com_altas para un ID de com_altas.
        """
        connection = None
        cursor = None

        try:
            connection = self._get_connection_interbus_365()
            cursor = connection.cursor(dictionary=True)
            processed_column = self._resolve_dfo_com_altas_processed_column(cursor)

            query = f"""
                SELECT
                    id,
                    etag,
                    personnel_number,
                    created_date,
                    {processed_column} AS procesado
                FROM dfo_com_altas
                WHERE id = %s
            """
            cursor.execute(query, (com_altas_id,))
            return cursor.fetchone()

        except Error as e:
            logger.error(f"Error obteniendo dfo_com_altas por id {com_altas_id}: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def update_dfo_com_altas_processed(self, com_altas_id: int, processed: int = 1) -> bool:
        """
        Actualiza el campo procesado en dfo_com_altas.
        """
        connection = None
        cursor = None

        try:
            connection = self._get_connection_interbus_365()
            cursor = connection.cursor()
            processed_column = self._resolve_dfo_com_altas_processed_column(cursor)

            query = f"UPDATE dfo_com_altas SET {processed_column} = %s WHERE id = %s"
            cursor.execute(query, (processed, com_altas_id))
            connection.commit()
            return cursor.rowcount > 0

        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Error actualizando dfo_com_altas procesado: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    def _resolve_trabajadores_nif_column(self, cursor) -> str:
        """
        Resuelve el nombre de columna de NIF/DNI en trabajadores.
        Prioriza 'nif' y cae a 'dni' si existe.
        """
        if self._trabajadores_nif_column:
            return self._trabajadores_nif_column

        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = 'trabajadores'
              AND column_name IN ('nif', 'dni')
            """,
            (self._database_e03800,)
        )
        columns = {row[0] for row in cursor.fetchall()}

        if 'nif' in columns:
            self._trabajadores_nif_column = 'nif'
        elif 'dni' in columns:
            self._trabajadores_nif_column = 'dni'
        else:
            self._trabajadores_nif_column = 'nif'

        return self._trabajadores_nif_column

    def _trabajador_exists(
        self,
        cursor,
        codiemp: str,
        nombre: str,
        apellido1: str,
        apellido2: str,
        nif_value: Optional[str],
        nif_column: str
    ) -> bool:
        """
        Verifica si existe un trabajador por identidad básica.
        """
        query = """
            SELECT 1
            FROM trabajadores
            WHERE codiemp = %s
              AND nombre = %s
              AND apellido1 = %s
              AND apellido2 = %s
        """
        params = [codiemp, nombre, apellido1, apellido2]

        nif_value_clean = str(nif_value).strip() if nif_value else ''
        if nif_value_clean:
            query += f" AND {nif_column} = %s"
            params.append(nif_value_clean)

        query += " LIMIT 1"
        cursor.execute(query, params)
        return cursor.fetchone() is not None

    def sync_trabajador_from_com_altas(
        self,
        data: Dict[str, Any],
        tipo: str,
        connection=None,
        cursor=None,
        nif_column: Optional[str] = None
    ) -> Optional[int]:
        """
        Inserta o actualiza un registro en trabajadores usando los datos de com_altas.

        Args:
            data: Diccionario con los datos de com_altas
            tipo: Tipo de registro ('A' o 'M')
            connection: Conexión opcional para reutilizar sesión
            cursor: Cursor opcional para reutilizar sesión
            nif_column: Columna de DNI/NIF en trabajadores

        Returns:
            int: ID del trabajador afectado, o None si no se pudo procesar
        """
        owns_connection = False

        if connection is None or cursor is None:
            connection = self._get_connection_e03800()
            cursor = connection.cursor()
            owns_connection = True

        try:
            coditraba_raw = str(data.get('coditraba') or '').strip()
            coditraba = None if coditraba_raw in ('', '0') else coditraba_raw
            codiemp = data.get('codiemp')
            puesto_cod = self.extract_codpuesto(data.get('puesto'))
            subpuesto_cod = self.extract_codpuesto(data.get('subpuesto'))
            puesto_concepto = self.resolve_puesto_concepto(
                codiemp,
                puesto_cod,
                "lista_puestos"
            )
            subpuesto_concepto = self.resolve_puesto_concepto(
                codiemp,
                subpuesto_cod,
                "lista_subpuestos"
            )

            if not nif_column:
                nif_column = self._resolve_trabajadores_nif_column(cursor)

            trabajador_data = {
                'codiemp': codiemp,
                'coditraba': coditraba,
                'nombre': data.get('nombre'),
                'apellido1': data.get('apellido1'),
                'apellido2': data.get('apellido2'),
                'fechaalta': data.get('fechaalta'),
                'fechaanti': data.get('fecha_antig'),
                'fechanaci': data.get('fechanacimiento'),
                'domicilio': data.get('domicilio'),
                'localidad': data.get('localidad'),
                'provincia': data.get('provincia'),
                'cpostal': data.get('cpostal'),
                'telefono': data.get('telefono'),
                'numeross': data.get('naf'),
                'banco': data.get('ccc'),
                'categoria': data.get('categoria_puesto'),
                'puesto': puesto_concepto or data.get('puesto'),
                'puesto2': subpuesto_concepto or data.get('subpuesto'),
                'nummat': data.get('nummat'),
                'contrato': data.get('tipo_contrato') or '',
                'id_usuario': data.get('id_usuario') or 0,
                'deptonomi': data.get('deptonomi') or '',
                'codocu': data.get('codocu') or ''
            }

            nif_value = data.get('nif')
            if nif_value is not None:
                trabajador_data[nif_column] = nif_value

            field_limits = {
                'codiemp': 5,
                'coditraba': 5,
                'nummat': 10,
                'nombre': 30,
                'apellido1': 30,
                'apellido2': 30,
                'domicilio': 60,
                'localidad': 30,
                'provincia': 30,
                'cpostal': 5,
                'telefono': 9,
                'numeross': 12,
                'banco': 40,
                'categoria': 20,
                'puesto': 40,
                'puesto2': 40,
                'contrato': 50,
                'deptonomi': 30,
                'codocu': 5
            }
            if nif_column:
                field_limits[nif_column] = 14

            for field, max_len in field_limits.items():
                if field in trabajador_data and trabajador_data[field] is not None:
                    trabajador_data[field] = self._truncate_str(trabajador_data[field], max_len)

            if tipo == 'M' and coditraba:
                cursor.execute(
                    """
                    SELECT id
                    FROM trabajadores
                    WHERE codiemp = %s AND coditraba = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (codiemp, coditraba)
                )
                row = cursor.fetchone()

                if row:
                    trabajador_id = row[0]
                    update_fields = {k: v for k, v in trabajador_data.items() if v is not None}

                    if not update_fields:
                        return trabajador_id

                    set_clause = ", ".join([f"{k} = %s" for k in update_fields])
                    values = list(update_fields.values())

                    query = f"UPDATE trabajadores SET {set_clause} WHERE id = %s"
                    cursor.execute(query, values + [trabajador_id])
                    connection.commit()

                    logger.info(f"Actualizado trabajador id: {trabajador_id}")
                    return trabajador_id

            fields = [k for k, v in trabajador_data.items() if v is not None]
            values = [trabajador_data[k] for k in fields]

            placeholders = ', '.join(['%s'] * len(fields))
            query = f"""
                INSERT INTO trabajadores ({', '.join(fields)})
                VALUES ({placeholders})
            """

            cursor.execute(query, values)
            connection.commit()

            trabajador_id = cursor.lastrowid
            logger.info(f"Insertado trabajador id: {trabajador_id}")
            return trabajador_id

        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Error sincronizando trabajador: {e}")
            raise
        finally:
            if owns_connection:
                if cursor:
                    cursor.close()
                if connection:
                    connection.close()

    def sync_trabajadores_from_com_altas(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Sincroniza trabajadores a partir de registros ALTA en com_altas.

        Args:
            limit: Límite de registros a procesar (None para todos)

        Returns:
            Dict con estadísticas del proceso
        """
        connection = None
        cursor = None

        stats = {
            'total': 0,
            'created': 0,
            'skipped': 0,
            'errors': 0
        }

        try:
            connection = self._get_connection_e03800()
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    id,
                    codiemp,
                    codicen,
                    coditraba,
                    nummat,
                    nif,
                    nombre,
                    apellido1,
                    apellido2,
                    fechaalta,
                    fecha_antig,
                    fechafincontrato,
                    fechanacimiento,
                    domicilio,
                    localidad,
                    provincia,
                    cpostal,
                    telefono,
                    naf,
                    ccc,
                    categoria_puesto,
                    puesto,
                    subpuesto,
                    tipo_contrato
                FROM com_altas
                WHERE tipo = 'A'
                ORDER BY id ASC
            """
            params = []
            if limit:
                query += " LIMIT %s"
                params.append(limit)

            cursor.execute(query, params)
            records = cursor.fetchall()
            stats['total'] = len(records)

            cursor.close()
            cursor = connection.cursor()

            nif_column = self._resolve_trabajadores_nif_column(cursor)
            interbus_connection = self._get_connection_interbus_365()
            interbus_cursor = interbus_connection.cursor(dictionary=True)
            processed_column = self._resolve_dfo_com_altas_processed_column(interbus_cursor)

            for record in records:
                com_altas_id = record.get('id')
                if not com_altas_id:
                    stats['skipped'] += 1
                    continue

                interbus_cursor.execute(
                    f"SELECT {processed_column} AS procesado FROM dfo_com_altas WHERE id = %s",
                    (com_altas_id,)
                )
                dfo_row = interbus_cursor.fetchone()
                if not dfo_row:
                    stats['skipped'] += 1
                    continue
                if int(dfo_row.get('procesado') or 0) != 0:
                    stats['skipped'] += 1
                    continue

                codiemp = record.get('codiemp')
                nombre = record.get('nombre')
                apellido1 = record.get('apellido1')
                apellido2 = record.get('apellido2') or ''
                nif_value = record.get('nif')

                if not codiemp or not nombre or not apellido1:
                    stats['skipped'] += 1
                    continue

                if self._trabajador_exists(cursor, codiemp, nombre, apellido1, apellido2, nif_value, nif_column):
                    stats['skipped'] += 1
                    continue

                self.sync_trabajador_from_com_altas(
                    record,
                    'A',
                    connection=connection,
                    cursor=cursor,
                    nif_column=nif_column
                )
                stats['created'] += 1

            return stats

        except Error as e:
            stats['errors'] += 1
            logger.error(f"Error sincronizando trabajadores desde com_altas: {e}")
            raise
        finally:
            if 'interbus_cursor' in locals() and interbus_cursor:
                interbus_cursor.close()
            if 'interbus_connection' in locals() and interbus_connection:
                interbus_connection.close()
            if cursor:
                cursor.close()
            if connection:
                connection.close()

