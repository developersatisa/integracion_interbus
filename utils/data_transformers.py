"""
Utilidades para transformar datos del endpoint EmployeeModifications a formato com_altas.
Maneja conversiones de tipos, fechas y valores NULL/vacíos.
"""
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

EDUCATION_LEVEL_CODE_BY_KEY = {
    "EDUCATIONFORTRAININGANDLABORINSERTIONREQUIREHIGHER": "53",
    "TRAININGANDLABORINSERTIONPROGRAMS": "21",
    "UNIVERSITYOWNEDDEGREESANDOTHERCOURSESREQUIREBACCALAUREATE": "52",
    "TRAININGANDLABORINSERTIONPROGRAMSREQUIREFIRSTSTAGESECONDARY": "31",
    "INCOMPLETEPRIMARYSTUDIES": "11",
    "UNIVERSITYDOCTORATE": "61",
    "TRAININGANDJOBPLACEMENT": "58",
    "HIGHERLEVELCOURSESFORSPECIFICANDEQUIVALENTVOCATIONAL": "51",
    "POSTGRADUATEEDUCATION": "57",
    "FIRSTSTAGESECONDARYEDUCATIONWITHHIGHSCHOOL": "23",
    "UNIVERSITYMASTERSDEGREES": "60",
    "COMPLETEPRIMARYSTUDIES": "12",
    "INTERMEDIATELEELCOURSESFORSPECIFICVOCATIONALTRAINING": "33",
    "INTERMEDIATELEVELCOURSESFORSPECIFICVOCATIONALTRAINING": "33",
    "SECONDCYCLEUNIVERSITYEDUCATION": "55",
    "NOTDEFINED": "00",
    "UNIVERSITYUNDERGRADUATEDEGREES": "59",
    "FIRSTSTAGESECONDARYEDUCATIONWITHOUTHIGHSCHOOL": "22",
    "BACCALAUREATECOURSES": "32",
    "FIRSTCYCLEUNIVERSITYEDUCATION": "54",
    "OFFICIALPROFESSIONALSPECIALIZATIONSTUDIES": "56",
    "COURSESFORTRAININGANDLABORINSERTIONTHATREQUIREA2": "41",
    "WITHOUTSTUDIES": "80",
}


def convert_string_to_int(value: str) -> Optional[int]:
    """
    Convierte string a int, retorna None si falla o está vacío.
    
    Args:
        value: Valor string a convertir
        
    Returns:
        int si la conversión es exitosa, None si falla o está vacío
    """
    if not value or value == '':
        return None
    try:
        return int(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Error convirtiendo '{value}' a int: {e}")
        return None


def convert_string_to_decimal(value: str) -> Optional[Decimal]:
    """
    Convierte string a decimal, retorna None si falla o está vacío.
    
    Args:
        value: Valor string a convertir
        
    Returns:
        Decimal si la conversión es exitosa, None si falla o está vacío
    """
    if not value or value == '':
        return None
    
    # Limpiar el valor: quitar espacios y convertir a string
    value_clean = str(value).strip()
    
    # Si el valor es texto no numérico (ej: "SALARIO"), retornar None sin warning
    if not value_clean.replace('.', '').replace(',', '').replace('-', '').isdigit():
        # Verificar si tiene formato numérico válido (puede tener punto decimal o coma)
        try:
            # Intentar convertir directamente
            return Decimal(value_clean.replace(',', '.'))
        except (ValueError, TypeError, InvalidOperation):
            # Si falla, es texto no numérico, retornar None silenciosamente
            return None
    
    try:
        # Reemplazar coma por punto para formato europeo
        value_normalized = value_clean.replace(',', '.')
        return Decimal(value_normalized)
    except (ValueError, TypeError, InvalidOperation) as e:
        logger.warning(f"Error convirtiendo '{value}' a decimal: {e}")
        return None


def normalize_gender(value: Optional[Any]) -> Optional[str]:
    """
    Normaliza el género para com_altas (Female -> M, Male -> V).
    """
    if value is None:
        return None
    value_str = str(value).strip()
    if not value_str:
        return None
    value_lower = value_str.lower()
    if value_lower == 'female':
        return 'M'
    if value_lower == 'male':
        return 'V'
    return value_str


def extract_date_from_datetime(datetime_str: str) -> Optional[str]:
    """
    Extrae solo la fecha de un datetime ISO, retorna None si falla.
    
    Args:
        datetime_str: String en formato datetime ISO (ej: "2025-01-01T14:52:34Z")
        
    Returns:
        String con fecha en formato YYYY-MM-DD, None si falla
    """
    if not datetime_str or datetime_str == '':
        return None
    try:
        # Manejar formato ISO con Z (UTC)
        dt_str = datetime_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(dt_str)
        return dt.date().isoformat()
    except (ValueError, AttributeError) as e:
        logger.warning(f"Error extrayendo fecha de '{datetime_str}': {e}")
        return None


def convert_datetime_iso_to_mysql(datetime_str: str) -> Optional[str]:
    """
    Convierte un datetime ISO a formato DATETIME de MySQL.
    
    Args:
        datetime_str: String en formato datetime ISO (ej: "2025-11-12T13:18:34Z")
        
    Returns:
        String en formato MySQL DATETIME (ej: "2025-11-12 13:18:34"), None si falla
    """
    if not datetime_str or datetime_str == '':
        return None
    try:
        # Manejar formato ISO con Z (UTC)
        dt_str = datetime_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(dt_str)
        # Formato MySQL DATETIME: YYYY-MM-DD HH:MM:SS
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, AttributeError) as e:
        logger.warning(f"Error convirtiendo datetime ISO a MySQL de '{datetime_str}': {e}")
        return None


def encode_etag_base64(etag: str) -> str:
    """
    Codifica un ETag en base64 para almacenarlo en la base de datos.
    
    Args:
        etag: ETag del endpoint (ej: 'W/\"JzEsNTYzNzE0NDU3OCc=\"')
        
    Returns:
        String codificado en base64
    """
    import base64
    if not etag:
        return ''
    try:
        return base64.b64encode(etag.encode('utf-8')).decode('utf-8')
    except Exception as e:
        logger.error(f"Error codificando ETag en base64: {e}")
        return ''


def normalize_etag(etag: str) -> str:
    """
    Normaliza el ETag eliminando escapes comunes de comillas.
    """
    if not etag:
        return ''
    return etag.replace('\\"', '"').replace("\\'", "'")


def decode_etag_base64(etag_base64: str) -> str:
    """
    Decodifica un ETag almacenado en base64.
    """
    import base64
    if not etag_base64:
        return ''
    try:
        decoded = base64.b64decode(etag_base64.encode('utf-8')).decode('utf-8')
        return normalize_etag(decoded)
    except Exception as e:
        logger.error(f"Error decodificando ETag base64: {e}")
        return ''


def normalize_null_or_empty(value: Any) -> Optional[Any]:
    """
    Normaliza valores NULL o vacíos a None.
    
    Args:
        value: Valor a normalizar
        
    Returns:
        None si el valor es None, vacío o string vacío, sino retorna el valor
    """
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == '':
        return None
    return value


def normalize_string(value: Any) -> Optional[str]:
    """
    Normaliza valores a string, retornando None si está vacío.
    """
    if value is None:
        return None
    if isinstance(value, str):
        value_str = value.strip()
    else:
        value_str = str(value)
    return value_str if value_str else None


def normalize_postal_code(value: Optional[Any], max_length: int = 5) -> Optional[str]:
    """
    Normaliza el código postal a longitud máxima.
    """
    value_str = normalize_string(value)
    if not value_str:
        return None
    digits_only = ''.join(ch for ch in value_str if ch.isdigit())
    if digits_only:
        return digits_only[:max_length]
    return value_str[:max_length]


def normalize_text_max(value: Optional[Any], max_length: int = 65535) -> Optional[str]:
    """
    Normaliza un texto a longitud máxima.
    """
    value_str = normalize_string(value)
    if not value_str:
        return None
    if len(value_str) <= max_length:
        return value_str
    logger.warning(f"Texto truncado a {max_length} caracteres")
    return value_str[:max_length]


def extract_ccc_from_codidepa(value: Optional[Any]) -> Optional[str]:
    """
    Extrae el CCC desde codidepa (formato esperado: codiemp-ccc).
    """
    value_str = normalize_string(value)
    if not value_str:
        return None
    if '-' in value_str:
        _, suffix = value_str.split('-', 1)
        return suffix or None
    return value_str


def normalize_education_level_code(value: Optional[Any]) -> Optional[str]:
    """
    Normaliza el nivel educativo: si llega en inglés, lo traduce al código numérico.
    """
    value_str = normalize_string(value)
    if not value_str:
        return None
    if value_str.isdigit():
        return value_str.zfill(2)
    key = ''.join(char for char in value_str.upper() if char.isalnum())
    mapped = EDUCATION_LEVEL_CODE_BY_KEY.get(key)
    if mapped is not None:
        return mapped
    logger.warning(f"Nivel educativo no reconocido: {value_str}")
    return None


def format_date_for_dynamics(value: Any) -> Optional[str]:
    """
    Convierte fechas a formato ISO esperado por Dynamics 365.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        dt_value = value.replace(microsecond=0)
        if dt_value.tzinfo is None:
            return dt_value.isoformat() + 'Z'
        return dt_value.isoformat()
    if isinstance(value, date):
        return value.strftime('%Y-%m-%dT00:00:00Z')

    value_str = str(value).strip()
    if not value_str:
        return None
    if len(value_str) == 10:
        return f"{value_str}T00:00:00Z"
    if ' ' in value_str and 'T' not in value_str:
        value_str = value_str.replace(' ', 'T')
    if value_str.endswith('Z') or '+' in value_str:
        return value_str
    return f"{value_str}Z"


def map_com_altas_to_employee_modifications(
    record: Dict[str, Any],
    processed_value: str = "Yes",
    personnel_number: Optional[str] = None,
    only_processed: bool = False
) -> Dict[str, Any]:
    """
    Mapea un registro de com_altas a formato EmployeeModifications para POST.
    """
    estado = normalize_string(record.get('estado'))
    estado_upper = estado.upper() if estado else ""
    is_denegado = estado_upper in {"D", "DENEGADO", "DENEGADA"}
    is_liquidado = estado_upper in {"L", "LIQUIDADO", "LIQUIDADA"}
    error_value = "Yes" if is_denegado else "No"
    correcto_value = "Yes" if is_liquidado else "No"
    error_description_value = normalize_text_max(record.get('observa_admin')) or ""

    if only_processed:
        return {
            'Processed': processed_value,
            'Error': error_value,
            'Correcto': correcto_value,
            'ErrorDescription': error_description_value
        }

    salario = record.get('salario')
    if isinstance(salario, Decimal):
        salario = str(salario)

    nummat = personnel_number or record.get('nummat')
    payload = {
        'CompanyIdATISA': normalize_string(record.get('codiemp')),
        'FirstName': normalize_string(record.get('nombre')),
        'LastName1': normalize_string(record.get('apellido1')),
        'LastName2': normalize_string(record.get('apellido2')),
        'Gender': normalize_string(record.get('sexo')),
        'NASS': normalize_string(record.get('naf')),
        'BirthDate': format_date_for_dynamics(record.get('fechanacimiento')),
        'Email': normalize_string(record.get('email')),
        'Phone': normalize_string(record.get('telefono')),
        'ZipCode': normalize_string(record.get('cpostal')),
        'StartDate': format_date_for_dynamics(record.get('fechaalta')),
        'Salary': salario,
        'BankAccount': normalize_string(record.get('ccc')),
        'PersonnelNumber': normalize_string(nummat),
        'HolidaysAbsencesGroupATISAId': normalize_string(record.get('grupo_vacaciones')),
        'LibrariesGroupATISAId': normalize_string(record.get('grupo_biblioteca')),
        'AdvanceGroupATISAId': normalize_string(record.get('grupo_anticipos')),
        'Street': normalize_string(record.get('domicilio')),
        'City': normalize_string(record.get('localidad')),
        'County': normalize_string(record.get('provincia')),
        'JobPositionIdATISA': normalize_string(record.get('categoria_puesto')),
        'ContractTypeID': normalize_string(record.get('tipo_contrato')),
        'EndDate': format_date_for_dynamics(record.get('fechafincontrato')),
        'Reasonforcontract': normalize_string(record.get('motivo_contrato')),
        'VATNum': normalize_string(record.get('nif')),
        'Processed': processed_value,
        'Error': error_value,
        'Correcto': correcto_value,
        'ErrorDescription': error_description_value
    }

    return {k: v for k, v in payload.items() if v is not None}


def map_com_altas_to_importfrom_atisas(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapea un registro de com_altas a formato ImportfromATISAs para POST.
    """
    payload = {
        "PersonnelNumber": normalize_string(record.get('nummat')),
        "CreatedDate": format_date_for_dynamics(datetime.utcnow()),
        "Street": normalize_string(record.get('domicilio')),
        "City": normalize_string(record.get('localidad')),
        "ZipCode": normalize_postal_code(record.get('cpostal')),
        "County": normalize_string(record.get('provincia')),
        "CountryRegionId": normalize_string(record.get('nacionalidad')),
        "Phone": normalize_string(record.get('telefono')),
        "Mobilephone": normalize_string(record.get('telmovil')),
        "Email": normalize_string(record.get('email')),
        "BankAccount": normalize_string(record.get('ccc'))
    }

    return {k: v for k, v in payload.items() if v is not None}


def is_numeric_string(value: str) -> bool:
    """
    Verifica si un string es numérico (puede contener punto o coma decimal).
    
    Args:
        value: String a verificar
        
    Returns:
        True si es numérico, False si no
    """
    if not value or not isinstance(value, str):
        return False
    
    value_clean = value.strip()
    if not value_clean:
        return False
    
    # Remover signo negativo al inicio si existe
    if value_clean.startswith('-'):
        value_clean = value_clean[1:]
    
    # Remover punto o coma decimal (solo uno)
    value_clean = value_clean.replace('.', '', 1).replace(',', '', 1)
    
    # Verificar si todos los caracteres restantes son dígitos
    return value_clean.isdigit()


def map_employee_to_com_altas(
    record: Dict[str, Any], 
    tipo: str, 
    coditraba: str,
    active_record: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Mapea un registro del endpoint EmployeeModifications a formato com_altas.
    
    Args:
        record: Registro del endpoint EmployeeModifications
        tipo: Tipo de registro ('A' para Alta, 'M' para Modificación)
        coditraba: Código de trabajador (0 para altas, código del trabajador para modificaciones)
        active_record: Registro activo de trabajadores (solo para MODIFICACIÓN, puede ser None)
        
    Returns:
        Dict con los datos mapeados para insertar en com_altas
    """
    # Procesar teléfono con lógica especial
    telefono_endpoint = normalize_null_or_empty(record.get('Phone'))
    telefono_final = None
    
    if telefono_endpoint:
        # Verificar si el teléfono del endpoint es numérico
        if is_numeric_string(str(telefono_endpoint)):
            telefono_final = telefono_endpoint
        else:
            # Si no es numérico y hay trabajador activo (MODIFICACIÓN), usar el de trabajadores
            if active_record and tipo == 'M':
                telefono_trabajador = active_record.get('telefono')
                if telefono_trabajador and is_numeric_string(str(telefono_trabajador)):
                    telefono_final = telefono_trabajador
                # Si tampoco es válido, queda None
            # Si es ALTA o no hay trabajador activo, queda None
    else:
        # Si el endpoint está vacío y hay trabajador activo (MODIFICACIÓN), usar el de trabajadores
        if active_record and tipo == 'M':
            telefono_trabajador = active_record.get('telefono')
            if telefono_trabajador and is_numeric_string(str(telefono_trabajador)):
                telefono_final = telefono_trabajador
        # Si no hay trabajador activo o no es válido, queda None

    # Procesar teléfono móvil con lógica similar al teléfono
    telmovil_endpoint = normalize_null_or_empty(record.get('Mobilephone'))
    telmovil_final = None
    max_int = 2147483647

    if telmovil_endpoint:
        if is_numeric_string(str(telmovil_endpoint)):
            telmovil_str = str(telmovil_endpoint).strip()
            if len(telmovil_str) <= 13:
                try:
                    telmovil_int = int(telmovil_str)
                    if telmovil_int <= max_int:
                        telmovil_final = str(telmovil_int)
                except ValueError:
                    telmovil_final = None
        else:
            if active_record and tipo == 'M':
                telmovil_trabajador = active_record.get('telmovil')
                if telmovil_trabajador and is_numeric_string(str(telmovil_trabajador)):
                    telmovil_str = str(telmovil_trabajador).strip()
                    if len(telmovil_str) <= 13:
                        try:
                            telmovil_int = int(telmovil_str)
                            if telmovil_int <= max_int:
                                telmovil_final = str(telmovil_int)
                        except ValueError:
                            telmovil_final = None
    else:
        if active_record and tipo == 'M':
            telmovil_trabajador = active_record.get('telmovil')
            if telmovil_trabajador and is_numeric_string(str(telmovil_trabajador)):
                telmovil_str = str(telmovil_trabajador).strip()
                if len(telmovil_str) <= 13:
                    try:
                        telmovil_int = int(telmovil_str)
                        if telmovil_int <= max_int:
                            telmovil_final = str(telmovil_int)
                    except ValueError:
                        telmovil_final = None

    # Procesar naf (NASS) con lógica especial (igual que telefono)
    nass_endpoint = normalize_null_or_empty(record.get('NASS'))
    naf_final = None
    
    if nass_endpoint:
        # Verificar si el NASS del endpoint es numérico
        if is_numeric_string(str(nass_endpoint)):
            naf_final = nass_endpoint
        else:
            # Si no es numérico y hay trabajador activo (MODIFICACIÓN), usar numeross de trabajadores
            if active_record and tipo == 'M':
                numeross_trabajador = active_record.get('numeross')
                if numeross_trabajador and is_numeric_string(str(numeross_trabajador)):
                    naf_final = numeross_trabajador
                # Si tampoco es válido, queda None
            # Si es ALTA o no hay trabajador activo, queda None
    else:
        # Si el endpoint está vacío y hay trabajador activo (MODIFICACIÓN), usar numeross de trabajadores
        if active_record and tipo == 'M':
            numeross_trabajador = active_record.get('numeross')
            if numeross_trabajador and is_numeric_string(str(numeross_trabajador)):
                naf_final = numeross_trabajador
        # Si no hay trabajador activo o no es válido, queda None
    
    # Procesar salario: solo verificar si es numérico
    salario_endpoint = normalize_null_or_empty(record.get('Salary', ''))
    salario_final = None
    
    if salario_endpoint:
        if is_numeric_string(str(salario_endpoint)):
            salario_final = convert_string_to_decimal(str(salario_endpoint))
        # Si no es numérico, queda None
    
    codiemp = normalize_null_or_empty(record.get('CompanyIdATISA'))
    education_level_raw = record.get('EducationLevel')
    if education_level_raw is None:
        education_level_raw = record.get('educationlevel')
    if education_level_raw is None:
        education_level_raw = record.get('LevelEducation')
    ccc_value = normalize_null_or_empty(record.get('BankAccount'))
    ccc_endpoint = normalize_null_or_empty(record.get('CCC'))
    codidepa_value = None
    if codiemp and ccc_endpoint:
        codidepa_value = f"{codiemp}-{ccc_endpoint}"
        if len(codidepa_value) > 30:
            codidepa_value = codidepa_value[:30]

    fechafincontrato_value = extract_date_from_datetime(record.get('EndDate', ''))
    if tipo in ('A', 'M'):
        fechafincontrato_value = None

    return {
        'codiemp': codiemp,
        'codicen': '001',
        'nombre': normalize_null_or_empty(record.get('FirstName')),
        'apellido1': normalize_null_or_empty(record.get('LastName1')),
        'apellido2': normalize_null_or_empty(record.get('LastName2')),
        'nif': normalize_null_or_empty(record.get('VATNum')),
        'sexo': normalize_gender(record.get('Gender')),
        'naf': naf_final,
        'fechanacimiento': extract_date_from_datetime(record.get('BirthDate', '')),
        'email': normalize_null_or_empty(record.get('Email')),
        'telefono': telefono_final,
        'telmovil': telmovil_final,
        'cpostal': normalize_postal_code(record.get('ZipCode')),
        'fechaalta': extract_date_from_datetime(record.get('StartDate', '')),
        'salario': salario_final,
        'ccc': ccc_value,
        'codidepa': codidepa_value,
        'nummat': normalize_null_or_empty(record.get('PersonnelNumber')),
        'grupo_vacaciones': convert_string_to_int(record.get('HolidaysAbsencesGroupATISAId', '')),
        'grupo_biblioteca': convert_string_to_int(record.get('LibrariesGroupATISAId', '')),
        'grupo_anticipos': convert_string_to_int(record.get('AdvanceGroupATISAId', '')),
        'grupo_incidencias': convert_string_to_int(record.get('IncidentGroupATISAId', '')),
        'tipo': tipo,
        'coditraba': coditraba,
        'titulacion': normalize_education_level_code(education_level_raw),
        
        # Campos de Dirección
        'domicilio': normalize_null_or_empty(record.get('Street')),
        'localidad': normalize_null_or_empty(record.get('City')),
        'provincia': normalize_null_or_empty(record.get('County')),
        'nacionalidad': normalize_null_or_empty(record.get('NationalityCountryRegion')),
        
        # Campos de Puesto y Contrato
        'puesto': normalize_null_or_empty(record.get('JobPositionIdATISA')),
        'subpuesto': normalize_null_or_empty(record.get('SubPosition')),
        'tipo_contrato': normalize_null_or_empty(record.get('ContractTypeID')),
        'fecha_antig': extract_date_from_datetime(record.get('SeniorityDate', '')),
        'fechafincontrato': fechafincontrato_value,
        'motivo_contrato': normalize_null_or_empty(record.get('Reasonforcontract')),
        'observaciones_modcon': normalize_text_max(record.get('Observations'))
    }

