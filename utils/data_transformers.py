"""
Utilidades para transformar datos del endpoint EmployeeModifications a formato com_altas.
Maneja conversiones de tipos, fechas y valores NULL/vacíos.
"""
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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
    
    return {
        'codiemp': normalize_null_or_empty(record.get('CompanyIdATISA')),
        'nombre': normalize_null_or_empty(record.get('FirstName')),
        'apellido1': normalize_null_or_empty(record.get('LastName1')),
        'apellido2': normalize_null_or_empty(record.get('LastName2')),
        'sexo': normalize_null_or_empty(record.get('Gender')),
        'naf': naf_final,
        'fechanacimiento': extract_date_from_datetime(record.get('BirthDate', '')),
        'email': normalize_null_or_empty(record.get('Email')),
        'telefono': telefono_final,
        'cpostal': normalize_null_or_empty(record.get('ZipCode')),
        'fechaalta': extract_date_from_datetime(record.get('StartDate', '')),
        'salario': salario_final,
        'ccc': normalize_null_or_empty(record.get('BankAccount')),
        'grupo_vacaciones': convert_string_to_int(record.get('HolidaysAbsencesGroupATISAId', '')),
        'grupo_biblioteca': convert_string_to_int(record.get('LibrariesGroupATISAId', '')),
        'grupo_anticipos': convert_string_to_int(record.get('AdvanceGroupATISAId', '')),
        'tipo': tipo,
        'coditraba': coditraba,
        
        # Campos de Dirección
        'domicilio': normalize_null_or_empty(record.get('Street')),
        'localidad': normalize_null_or_empty(record.get('City')),
        'provincia': normalize_null_or_empty(record.get('County')),
        'nacionalidad': convert_string_to_int(record.get('CountryRegionId', '')),
        
        # Campos de Puesto y Contrato
        'categoria_puesto': normalize_null_or_empty(record.get('JobPositionIdATISA')),
        'tipo_contrato': normalize_null_or_empty(record.get('ContractTypeID')),
        'fecha_antig': extract_date_from_datetime(record.get('SeniorityDate', '')),
        'fechafincontrato': extract_date_from_datetime(record.get('EndDate', '')),
        'motivo_contrato': normalize_null_or_empty(record.get('Reasonforcontract'))
    }

