"""
Adaptador para la base de datos e03800.
Implementa las operaciones necesarias para obtener datos de gruposervicios y archivos DBF.
"""
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional
from config.settings import settings
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class E03800DatabaseAdapter:
    """Adaptador para interactuar con la base de datos e03800 y archivos DBF."""
    
    def __init__(self):
        self._host = settings.db_host
        self._port = settings.db_port
        self._user = settings.db_user
        self._password = settings.db_password
        self._database = "e03800"  # Base de datos específica
        self._dbf_base_path = "/mnt/tierra_laboral_atinomi/"  # Ruta base para archivos DBF
        self._trabajadores_nif_column = None
    
    def _get_connection(self):
        """Obtiene una conexión a la base de datos e03800."""
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
            logger.error(f"Error conectando a MySQL e03800: {e}")
            raise

    def _resolve_trabajadores_nif_column(self, connection) -> str:
        """
        Resuelve el nombre de columna de NIF/DNI en trabajadores.
        Prioriza 'nif' y cae a 'dni' si existe.
        """
        if self._trabajadores_nif_column:
            return self._trabajadores_nif_column

        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = 'trabajadores'
                  AND column_name IN ('nif', 'dni')
                """,
                (self._database,)
            )
            columns = {row[0] for row in cursor.fetchall()}
        finally:
            cursor.close()

        if 'nif' in columns:
            self._trabajadores_nif_column = 'nif'
        elif 'dni' in columns:
            self._trabajadores_nif_column = 'dni'
        else:
            self._trabajadores_nif_column = 'nif'

        return self._trabajadores_nif_column
    
    def get_gruposervicios_by_service(self, id_servicios: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los registros de gruposervicios filtrando por id_servicios.
        Retorna lista con id y nombre.
        
        Args:
            id_servicios: Identificador del servicio (p.ej., 30 vacaciones, 10 incidencias)
        
        Returns:
            Lista de diccionarios con 'id' y 'nombre'
        """
        connection = None
        cursor = None
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT id, nombre
                FROM gruposervicios
                WHERE id_servicios = %s
                ORDER BY id
            """
            
            cursor.execute(query, (id_servicios,))
            results = cursor.fetchall()
            
            # Convertir a formato estándar
            gruposervicios = []
            for row in results:
                gruposervicios.append({
                    'id': str(row['id']),
                    'nombre': row['nombre']
                })
            
            logger.info(f"Obtenidos {len(gruposervicios)} registros de gruposervicios (id_servicios={id_servicios})")
            
            return gruposervicios
            
        except Error as e:
            logger.error(f"Error obteniendo gruposervicios: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_vacation_calendars_current_year(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los registros de vac_calendarios del año actual.
        Retorna lista con codigo y nombre.
        
        Returns:
            Lista de diccionarios con 'id' (codigo) y 'nombre'
        """
        connection = None
        cursor = None
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT codigo, nombre
                FROM vac_calendarios
                WHERE anio = YEAR(CURDATE())
                ORDER BY codigo
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Convertir a formato estándar
            calendars = []
            for row in results:
                calendars.append({
                    'id': str(row['codigo']),
                    'nombre': row['nombre']
                })
            
            logger.info(f"Obtenidos {len(calendars)} registros de vac_calendarios (año actual)")
            
            return calendars
            
        except Error as e:
            logger.error(f"Error obteniendo calendarios de vacaciones: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_empresas(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los registros de empresas.
        Retorna lista con codiemp y nombre.
        
        Returns:
            Lista de diccionarios con 'id' (codiemp) y 'nombre'
        """
        connection = None
        cursor = None
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT
                    e.codiemp,
                    e.nombre,
                    e.cif,
                    c.ccc
                FROM empresas e
                LEFT JOIN (
                    SELECT codiemp, MAX(ccc) AS ccc
                    FROM ccc
                    WHERE tipo = 'Principal'
                    GROUP BY codiemp
                ) c ON c.codiemp = e.codiemp
                ORDER BY e.codiemp
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Convertir a formato estándar
            empresas = []
            for row in results:
                empresas.append({
                    'id': str(row['codiemp']),
                    'nombre': row['nombre'],
                    'cif': str(row.get('cif') or '').strip(),
                    'quotation_account': str(row.get('ccc') or '').strip()
                })
            
            logger.info(f"Obtenidos {len(empresas)} registros de empresas")
            
            return empresas
            
        except Error as e:
            logger.error(f"Error obteniendo empresas: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_worker_places(self) -> List[Dict[str, Any]]:
        """
        Obtiene registros de WorkerPlaces desde la DBF contrcen.dbf.
        
        Lógica:
        1. Obtiene codigop de la tabla empresas (tabla e03800.empresas)
        2. Lee contrcen.dbf filtrando por esos codigop
        3. EQMWorkerPlaceID = codigop + codigodom
        4. Description = via + " " + calle + " " + CPOSAL + " " + Municipio + " " + Provincia
        5. Retorna solo registros donde codigop esté en empresas
        
        Returns:
            Lista de diccionarios con 'id' (codigop+codigodom) y 'nombre' (description)
        """
        try:
            from dbfread import DBF
        except ImportError:
            logger.error("dbfread no está instalado. Instálalo con: pip install dbfread")
            raise
        
        worker_places = []
        
        try:
            # 1. Obtener códigos de empresas
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # El campo correcto en empresas es 'codiemp'
            query = "SELECT DISTINCT codiemp FROM empresas WHERE codiemp IS NOT NULL AND codiemp != ''"
            cursor.execute(query)
            codigos_result = cursor.fetchall()
            codigos_validos = {str(row['codiemp']).strip() for row in codigos_result if row.get('codiemp')}
            
            cursor.close()
            connection.close()
            
            if not codigos_validos:
                return []
            
            logger.info(f"✓ Códigos de empresas válidos: {len(codigos_validos)}")
            
            # 2. Leer contrcen.dbf
            dbf_path = Path(self._dbf_base_path) / "contrcen.dbf"
            
            # Buscar archivo con diferentes casos
            if not dbf_path.exists():
                candidates = []
                for name in ["CONTRCEN.DBF", "Contrcen.dbf", "CONTRcen.dbf"]:
                    p = Path(self._dbf_base_path) / name
                    if p.exists():
                        candidates.append(p)
                        break
                if not candidates:
                    raise FileNotFoundError(f"Archivo contrcen.dbf no encontrado en {self._dbf_base_path}")
                dbf_path = candidates[0]
            
            logger.info(f"✓ Leyendo DBF: {dbf_path}")
            
            # 3. Leer DBF en modo lectura
            # load=True: carga todos los registros en memoria para mayor velocidad
            # char_decode_errors='ignore': ignora errores de codificación
            table = DBF(str(dbf_path), load=True, char_decode_errors='ignore')
            
            logger.info(f"✓ Total registros en DBF: {len(table)}")
            
            # DEBUG: Verificar campos disponibles en el DBF
            first_record = None
            for rec in table:
                first_record = rec
                break
            
            if first_record:
                available_fields = list(first_record.keys())
                logger.info(f"🔍 DEBUG: Campos disponibles en DBF: {available_fields}")
                
                # Verificar algunos valores del primer registro
                logger.info(f"🔍 DEBUG: Primer registro completo: {dict(first_record)}")
            
            # Reiniciar la iteración del DBF para procesar todos los registros
            table = DBF(str(dbf_path), load=True, char_decode_errors='ignore')
            
            # 4. Procesar registros
            sample_codigops = set()
            matching_count = 0
            
            for idx, rec in enumerate(table, 1):
                try:
                    # Obtener codigop y validar (usar CODIGOP en mayúsculas)
                    codigop_raw = rec.get('CODIGOP')
                    codigop = str(codigop_raw or '').strip() if codigop_raw is not None else ''
                    
                    # Guardar muestras para debugging (primeros 20)
                    if idx <= 20:
                        sample_codigops.add(codigop)
                    
                    # Filtrar solo los que están en empresas
                    if not codigop or codigop not in codigos_validos:
                        continue
                    
                    matching_count += 1
                    
                    # Obtener codigodom (usar CODIGODOM en mayúsculas)
                    codigodom = str(rec.get('CODIGODOM') or '').strip()
                    
                    # EQMWorkerPlaceID = codigop + codigodom
                    worker_place_id = f"{codigop}{codigodom}"
                    
                    # Description = via + " " + calle + " " + CPOSTAL + " " + MUNICIPIO + " " + PROVINCIA
                    # Usar mayúsculas para los nombres de campos
                    via = str(rec.get('VIA') or '').strip()
                    calle = str(rec.get('CALLE') or '').strip()
                    cpostal = str(rec.get('CPOSTAL') or '').strip()
                    municipio = str(rec.get('MUNICIPIO') or '').strip()
                    provincia = str(rec.get('PROVINCIA') or '').strip()
                    
                    # Concatenar con espacios
                    description_parts = [part for part in [via, calle, cpostal, municipio, provincia] if part]
                    description = ' '.join(description_parts) if description_parts else worker_place_id
                    
                    worker_places.append({
                        'id': worker_place_id,
                        'nombre': description,
                        'codiemp': codigop
                    })
                    
                except Exception as e:
                    continue
            
            # Logs de debugging
            logger.info(f"\n🔍 DEBUG: Primeros 20 codigop del DBF: {sorted(sample_codigops)}")
            logger.info(f"🔍 DEBUG: Todos los codiemp de empresas ({len(codigos_validos)}): {sorted(list(codigos_validos))}")
            logger.info(f"🔍 DEBUG: Coincidencias encontradas: {matching_count}")
            
            # Verificar si hay algún overlap
            codigop_set = {codigop for codigop in sample_codigops if codigop}
            overlap = codigop_set & codigos_validos
            if overlap:
                pass
            else:
                pass
            
            logger.info(f"✓ Obtenidos {len(worker_places)} registros de WorkerPlaces válidos")
            logger.info(f"  Filtrados {len(table) - len(worker_places)} registros (codigop no está en empresas)")
            
            return worker_places
            
        except Exception as e:
            logger.error(f"Error obteniendo WorkerPlaces: {e}", exc_info=True)
            raise
    
    def get_gruposervicio_by_id(self, grupo_id: str, id_servicios: int = 30) -> Dict[str, Any]:
        """
        Obtiene un registro de gruposervicios por ID.
        
        Args:
            grupo_id: ID del grupo
            id_servicios: Filtro de servicio
            
        Returns:
            Diccionario con id y nombre, o None si no existe
        """
        connection = None
        cursor = None
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT id, nombre
                FROM gruposervicios
                WHERE id = %s AND id_servicios = %s
            """
            
            cursor.execute(query, (grupo_id, id_servicios))
            result = cursor.fetchone()
            
            if result:
                return {
                    'id': str(result['id']),
                    'nombre': result['nombre']
                }
            
            return None
            
        except Error as e:
            logger.error(f"Error obteniendo gruposervicio por ID: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_contribution_account_code_ccs(self) -> List[Dict[str, Any]]:
        """
        Obtiene registros de ContributionAccountCodeCCs combinando datos de:
        - e03800.ccc (campo ccc) → EQMCCC
        - contrcen.dbf (CODIGOP + CODIGODOM) → EQMWorkerPlaceID
        
        Lógica:
        1. Obtiene todos los ccc de la tabla e03800.ccc (asocia codiemp con ccc)
        2. Lee contrcen.dbf filtrando por codiemp que estén en empresas
        3. Por cada contrcen.dbf con codigop que exista en ccc.codiemp, crea registro
        4. EQMWorkerPlaceID = codigop + codigodom
        5. EQMCCC = ccc.ccc donde codigop = ccc.codiemp
        
        Returns:
            Lista de diccionarios con 'id', 'nombre', 'eqmccc', 'eqmworkerplaceid'
        """
        try:
            from dbfread import DBF
        except ImportError:
            logger.error("dbfread no está instalado. Instálalo con: pip install dbfread")
            raise
        
        contribution_codes = []
        
        try:
            # 1. Obtener todos los ccc de la tabla ccc
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Obtener codiemp que están en empresas (mismo filtro que WorkerPlaces)
            query = "SELECT DISTINCT codiemp FROM empresas WHERE codiemp IS NOT NULL AND codiemp != ''"
            cursor.execute(query)
            empresas_result = cursor.fetchall()
            codigos_empresas = {str(row['codiemp']).strip() for row in empresas_result if row.get('codiemp')}
            
            logger.info(f"✓ Códigos de empresas válidos: {len(codigos_empresas)}")
            
            # Obtener todos los CCC con su CIF de empresa
            query = """
                SELECT c.codiemp, c.ccc, e.cif 
                FROM ccc c
                LEFT JOIN empresas e ON c.codiemp = e.codiemp
                WHERE c.codiemp IS NOT NULL AND c.codiemp != '' 
                  AND c.ccc IS NOT NULL AND c.ccc != ''
            """
            cursor.execute(query)
            ccc_result = cursor.fetchall()
            
            # Crear diccionario codiemp -> {ccc, cif}
            ccc_dict = {}
            for row in ccc_result:
                codiemp = str(row['codiemp']).strip()
                ccc = str(row['ccc']).strip()
                cif = str(row.get('cif') or '').strip()
                if codiemp and ccc:
                    ccc_dict[codiemp] = {'ccc': ccc, 'cif': cif}
            
            cursor.close()
            connection.close()
            
            logger.info(f"✓ CCC disponibles: {len(ccc_dict)}")
            
            if not codigos_empresas:
                return []
            
            # 2. Leer contrcen.dbf
            dbf_path = Path(self._dbf_base_path) / "contrcen.dbf"
            
            # Buscar archivo con diferentes casos
            if not dbf_path.exists():
                candidates = []
                for name in ["CONTRCEN.DBF", "Contrcen.dbf", "CONTRcen.dbf"]:
                    p = Path(self._dbf_base_path) / name
                    if p.exists():
                        candidates.append(p)
                        break
                if not candidates:
                    raise FileNotFoundError(f"Archivo contrcen.dbf no encontrado en {self._dbf_base_path}")
                dbf_path = candidates[0]
            
            logger.info(f"✓ Leyendo DBF: {dbf_path}")
            
            # 3. Leer DBF
            table = DBF(str(dbf_path), load=True, char_decode_errors='ignore')
            
            logger.info(f"✓ Total registros en DBF: {len(table)}")
            
            # 4. Procesar registros
            matching_count = 0
            
            for idx, rec in enumerate(table, 1):
                try:
                    # Obtener codigop
                    codigop_raw = rec.get('CODIGOP')
                    codigop = str(codigop_raw or '').strip() if codigop_raw is not None else ''
                    
                    # Filtrar: debe estar en empresas Y en ccc
                    if not codigop or codigop not in codigos_empresas:
                        continue
                    
                    # Verificar si tiene CCC asociado
                    if codigop not in ccc_dict:
                        continue
                    
                    matching_count += 1
                    
                    # Obtener codigodom
                    codigodom = str(rec.get('CODIGODOM') or '').strip()
                    
                    # EQMWorkerPlaceID = codigop + codigodom
                    # Si codigodom está vacío, usar solo codigop
                    eqm_worker_place_id = f"{codigop}{codigodom}" if codigodom else codigop
                    
                    # EQMCCC = ccc correspondiente a este codigop
                    ccc_data = ccc_dict[codigop]
                    eqm_ccc = ccc_data['ccc']
                    cif = ccc_data['cif']
                    
                    # El id será la combinación de ambos campos (unique en Dynamics)
                    unique_id = f"{eqm_ccc}_{eqm_worker_place_id}"
                    
                    contribution_codes.append({
                        'id': unique_id,
                        'nombre': f"CCC {eqm_ccc} para {eqm_worker_place_id}",
                        'eqmccc': eqm_ccc,
                        'eqmworkerplaceid': eqm_worker_place_id,
                        'cif': cif
                    })
                    
                except Exception as e:
                    continue
            
            logger.info(f"✓ Coincidencias encontradas: {matching_count}")
            logger.info(f"✓ Obtenidos {len(contribution_codes)} registros de ContributionAccountCodeCCs válidos")
            
            return contribution_codes
            
        except Exception as e:
            logger.error(f"Error obteniendo ContributionAccountCodeCCs: {e}", exc_info=True)
            raise


    def get_vacation_balances(self) -> List[Dict[str, Any]]:
        """
        Obtiene registros para la entidad VacationBalances desde el archivo DBF convvaca.dbf,
        filtrando por empresas válidas (e03800.empresas.codiemp).

        EQMVacationBalanceId = Codigop + " -> " + INT(DIAS) + TIPO + " " + AD_DIAS1 + AD_MOD1 + " (" + ID + ")"

        Returns:
            Lista de diccionarios con 'id' y 'nombre' (se usa el mismo valor que id)
        """
        try:
            from dbfread import DBF
        except ImportError:
            logger.error("dbfread no está instalado. Instálalo con: pip install dbfread")
            raise

        connection = None
        cursor = None
        try:
            # 1. Obtener todas las empresas válidas de MySQL
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute("""
                SELECT DISTINCT codiemp
                FROM empresas
                WHERE codiemp IS NOT NULL AND codiemp <> ''
            """)
            empresas = {str(r['codiemp']).strip() for r in cursor.fetchall() if r.get('codiemp')}

            if not empresas:
                logger.warning("No se encontraron empresas válidas en MySQL para filtrar VacationBalances")
                return []

            # 2. Localizar el archivo DBF
            dbf_path = Path(self._dbf_base_path) / "convvaca.dbf"
            if not dbf_path.exists():
                candidates = []
                for name in ["CONVVACA.DBF", "Convvaca.dbf", "CONVvaca.dbf"]:
                    p = Path(self._dbf_base_path) / name
                    if p.exists():
                        candidates.append(p)
                        break
                if not candidates:
                    # Intentar con la versión en plural por si acaso
                    for name in ["CONVVACAS.DBF", "Convvacas.dbf", "convvacas.dbf"]:
                        p = Path(self._dbf_base_path) / name
                        if p.exists():
                            candidates.append(p)
                            break
                
                if not candidates:
                    raise FileNotFoundError(f"Archivo convvaca.dbf no encontrado en {self._dbf_base_path}")
                dbf_path = candidates[0]

            logger.info(f"✓ Leyendo VacationBalances desde DBF: {dbf_path}")

            # 3. Leer el archivo DBF
            table = DBF(str(dbf_path), load=True, char_decode_errors='ignore')
            logger.info(f"✓ Total registros en DBF {dbf_path.name}: {len(table)}")

            results: List[Dict[str, Any]] = []
            for row in table:
                # Los campos en DBF suelen estar en mayúsculas
                codigop = str(row.get('CODIGOP') or '').strip()
                if not codigop or codigop not in empresas:
                    continue

                # Extraer campos para el identificador
                # DIAS suele ser numérico en DBF, lo pasamos a entero
                dias_val = row.get('DIAS')
                try:
                    dias_int = int(float(dias_val)) if dias_val is not None else 0
                except (ValueError, TypeError):
                    dias_int = 0
                
                tipo = str(row.get('TIPO') or '').strip()
                ad_dias1 = str(row.get('AD_DIAS1') or '').strip()
                ad_mod1 = str(row.get('AD_MOD1') or '').strip()
                rec_id = str(row.get('ID') or '').strip()

                identifier = f"{codigop} -> {dias_int}{tipo} {ad_dias1}{ad_mod1} ({rec_id})"

                results.append({
                    'id': identifier,
                    'nombre': identifier
                })

            logger.info(f"✓ Obtenidos {len(results)} registros de VacationBalances válidos")
            return results

        except Exception as e:
            logger.error(f"Error obteniendo VacationBalances desde DBF: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def _fetch_trabajador_records(
        self,
        connection,
        where_clause: str,
        params: tuple
    ) -> List[Dict[str, Any]]:
        cursor = connection.cursor(dictionary=True)
        try:
            nif_column = self._resolve_trabajadores_nif_column(connection)
            query = f"""
                SELECT coditraba, fechaalta, fechabaja, telefono, numeross, {nif_column} AS nif
                FROM trabajadores
                WHERE {where_clause}
                ORDER BY fechaalta DESC
            """
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            cursor.close()

    def _build_trabajador_info(
        self,
        records: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        if not records:
            return None

        active_record = None
        has_active = False

        for record in records:
            fechabaja = record.get('fechabaja')
            if fechabaja is None or fechabaja == '':
                has_active = True
                if active_record is None:
                    active_record = record

        return {
            'exists': True,
            'has_active': has_active,
            'active_record': active_record,
            'all_records': records
        }
    
    def find_trabajador(self, codiemp: str, nombre: str, apellido1: str, apellido2: str) -> Optional[Dict[str, Any]]:
        """
        Busca un trabajador en la tabla trabajadores.
        Un trabajador puede tener MÚLTIPLES registros.
        
        Args:
            codiemp: Código de empresa
            nombre: Nombre del trabajador
            apellido1: Primer apellido
            apellido2: Segundo apellido
        
        Returns:
            None si no existe ningún registro
            Dict con:
                - 'exists': True
                - 'has_active': True/False (si hay al menos un registro con fechabaja = NULL o vacío)
                - 'active_record': Dict con datos del registro activo (si existe) o None
                    - Incluye: coditraba, fechaalta, fechabaja, telefono, numeross, nif
                - 'all_records': List[Dict] con TODOS los registros del trabajador
        """
        connection = None
        
        try:
            connection = self._get_connection()
            records = self._fetch_trabajador_records(
                connection,
                "codiemp = %s AND nombre = %s AND apellido1 = %s AND apellido2 = %s",
                (codiemp, nombre, apellido1, apellido2)
            )
            return self._build_trabajador_info(records)
            
        except Error as e:
            logger.error(f"Error buscando trabajador: {e}")
            raise
        finally:
            if connection:
                connection.close()

    def find_trabajador_by_nass(self, codiemp: str, nass: str) -> Optional[Dict[str, Any]]:
        """
        Busca un trabajador por NASS (numeross) dentro de una empresa.
        """
        connection = None

        try:
            connection = self._get_connection()
            records = self._fetch_trabajador_records(
                connection,
                "codiemp = %s AND numeross = %s",
                (codiemp, nass)
            )
            return self._build_trabajador_info(records)

        except Error as e:
            logger.error(f"Error buscando trabajador por NASS: {e}")
            raise
        finally:
            if connection:
                connection.close()

    def find_trabajador_by_nif(self, codiemp: str, nif: str) -> Optional[Dict[str, Any]]:
        """
        Busca un trabajador por NIF/DNI dentro de una empresa.
        """
        connection = None

        try:
            connection = self._get_connection()
            nif_column = self._resolve_trabajadores_nif_column(connection)
            records = self._fetch_trabajador_records(
                connection,
                f"codiemp = %s AND {nif_column} = %s",
                (codiemp, nif)
            )
            return self._build_trabajador_info(records)

        except Error as e:
            logger.error(f"Error buscando trabajador por NIF: {e}")
            raise
        finally:
            if connection:
                connection.close()
    
    def get_last_fechabaja(self, codiemp: str, nombre: str, apellido1: str, apellido2: str) -> Optional[str]:
        """
        Obtiene la última fecha de baja de un trabajador.
        Un trabajador puede tener MÚLTIPLES registros, necesitamos iterar por todos.
        
        Args:
            codiemp: Código de empresa
            nombre: Nombre del trabajador
            apellido1: Primer apellido
            apellido2: Segundo apellido
        
        Returns:
            None si no hay registros con fechabaja
            String con la fecha de baja más reciente (más grande)
        """
        connection = None
        cursor = None
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Obtener TODOS los registros del trabajador con fechabaja
            query = """
                SELECT fechabaja
                FROM trabajadores
                WHERE codiemp = %s 
                  AND nombre = %s 
                  AND apellido1 = %s 
                  AND apellido2 = %s
                  AND fechabaja IS NOT NULL
                  AND fechabaja != ''
                ORDER BY fechabaja DESC
            """
            cursor.execute(query, (codiemp, nombre, apellido1, apellido2))
            records_with_baja = cursor.fetchall()
            
            if not records_with_baja:
                return None
            
            # Iterar por TODOS los registros para encontrar la fecha más reciente
            # Aunque están ordenados DESC, iteramos para asegurarnos
            last_fechabaja = None
            
            for record in records_with_baja:
                fechabaja = record.get('fechabaja')
                if fechabaja:
                    # Comparar fechas (asumiendo formato DATE o DATETIME)
                    if last_fechabaja is None:
                        last_fechabaja = fechabaja
                    else:
                        # Comparar fechas: la más reciente es la mayor
                        if fechabaja > last_fechabaja:
                            last_fechabaja = fechabaja
            
            return last_fechabaja
            
        except Error as e:
            logger.error(f"Error obteniendo última fecha de baja: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_last_fechabaja_by_nass(self, codiemp: str, nass: str) -> Optional[str]:
        """
        Obtiene la última fecha de baja de un trabajador filtrando por NASS (numeross).
        """
        connection = None
        cursor = None

        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT fechabaja
                FROM trabajadores
                WHERE codiemp = %s
                  AND numeross = %s
                  AND fechabaja IS NOT NULL
                  AND fechabaja != ''
                ORDER BY fechabaja DESC
                LIMIT 1
            """
            cursor.execute(query, (codiemp, nass))
            row = cursor.fetchone()
            return row.get('fechabaja') if row else None
        except Error as e:
            logger.error(f"Error obteniendo última fechabaja por NASS: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_last_fechabaja_by_nif(self, codiemp: str, nif: str) -> Optional[str]:
        """
        Obtiene la última fecha de baja de un trabajador filtrando por NIF/DNI.
        """
        connection = None
        cursor = None

        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)
            nif_column = self._resolve_trabajadores_nif_column(connection)
            query = f"""
                SELECT fechabaja
                FROM trabajadores
                WHERE codiemp = %s
                  AND {nif_column} = %s
                  AND fechabaja IS NOT NULL
                  AND fechabaja != ''
                ORDER BY fechabaja DESC
                LIMIT 1
            """
            cursor.execute(query, (codiemp, nif))
            row = cursor.fetchone()
            return row.get('fechabaja') if row else None
        except Error as e:
            logger.error(f"Error obteniendo última fechabaja por NIF: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

