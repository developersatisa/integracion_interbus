# Guía de Trabajo con Archivos DBF en Python

## Índice
1. [Introducción](#introducción)
2. [Librerías Utilizadas](#librerías-utilizadas)
3. [Estructura de PLAN de DBF](#estructura-del-proyecto)
4. [Lectura de Archivos DBF (Solo Lectura)](#lectura-de-archivos-dbf-solo-lectura)
5. [Lectura y Escritura de Archivos DBF (Modo RW)](#lectura-y-escritura-de-archivos-dbf-modo-rw)
6. [Operaciones Específicas del Proyecto](#operaciones-específicas-del-proyecto)
7. [Configuración del Proyecto](#configuración-del-proyecto)
8. [Gestión de Rutas y Traducción de Unidades](#gestión-de-rutas-y-traducción-de-unidades)
9. [Manejo de Errores y Validaciones](#manejo-de-errores-y-validaciones)
10. [Mejores Prácticas](#mejores-prácticas)
11. [Ejemplos Completos de Uso](#ejemplos-completos-de-uso)

---

## Introducción

Este documento describe cómo trabajar con archivos DBF (dBase/FoxPro) en python. 

El proyecto utiliza dos librerías diferentes según la operación:
- **`dbfread`**: Para operaciones de solo lectura (más rápida y eficiente)
- **`dbf`**: Para operaciones de lectura/escritura (más completa pero más lenta)

---

## Librerías Utilizadas

### Requisitos (requirements.txt)

```txt
dbfread==2.0.7  # Solo lectura - rápida y eficiente
dbf==0.99.11    # Lectura y escritura - completa pero más lenta
```

### Importación

```python
# Para operaciones de solo lectura
from dbfread import DBF

# Para operaciones de lectura/escritura
import dbf as dbfw
```


### Busqueda Case-Insensitive

El código busca archivos DBF sin importar mayúsculas/minúsculas:

```python
candidates = []
for name in ["empresas.dbf", "EMPRESAS.DBF", "Empresas.dbf"]:
    p = Path(base_dir) / name
    if p.exists():
        candidates.append(p)
```

---

## Lectura de Archivos DBF (Solo Lectura)

### Sintaxis Básica con dbfread

```python
from dbfread import DBF
from pathlib import Path

# Crear objeto DBF
table = DBF(dbf_path.as_posix(), load=True, char_decode_errors='ignore')

# Iterar sobre registros
for rec in table:
    # Acceder a campos (case-sensitive por defecto)
    nif = str(rec.get('NIF_CIF') or '').strip()
    
    # Manejar campos opcionales
    ubicacion = str(rec.get('UBICACION') or '').strip()
    empresa = str(rec.get('EMPRESA') or '').strip()
```

### Parámetros Importantes

- **`load=True`**: Carga todos los registros en memoria (más rápido para archivos pequeños)
- **`char_decode_errors='ignore'`**: Ignora errores de codificación de caracteres

### Ejemplo: Leer EMPRESAS.DBF

```python
def leer_empresas(base_dir):
    empresas_info = {}
    
    # Buscar archivo DBF
    candidates = []
    for name in ["empresas.dbf", "EMPRESAS.DBF", "Empresas.dbf"]:
        p = Path(base_dir) / name
        if p.exists():
            candidates.append(p)
            break
    
    if not candidates:
        return empresas_info
    
    empresas_path = candidates[0]
    
    # Leer DBF
    from dbfread import DBF
    table = DBF(empresas_path.as_posix(), load=True, char_decode_errors='ignore')
    
    # Procesar registros
    for rec in table:
        nif = str(rec.get('NIF_CIF') or '').strip()
        
        if not nif:
            continue
        
        # Normalizar CIF (eliminar caracteres especiales, mayúsculas)
        key = re.sub(r"\W", "", nif.upper())
        
        empresas_info[key] = {
            'UBICACION': str(rec.get('UBICACION') or '').strip(),
            'EMPRESA': str(rec.get('EMPRESA') or '').strip(),
        }
    
    return empresas_info
```

### Trabajar con Fechas

Los campos de fecha en DBF se manejan automáticamente como objetos `date`:

```python
f1 = rec.get('Fecha') or rec.get('FECHA')  # date o None
f2 = rec.get('Fecha2') or rec.get('FECHA2')

# Comparar fechas
if fa_dt and f1 and f2 and (f1 <= fa_dt <= f2):
    # La fecha está en el rango
    val = rec.get('codigop') or rec.get('CODIGOP')
```

---

## Lectura y Escritura de Archivos DBF (Modo RW)

### Sintaxis Básica con dbf

```python
import dbf as dbfw
from pathlib import Path

# Abrir tabla en modo lectura/escritura
tbl = dbfw.Table(dbf_path.as_posix())
tbl.open(mode=dbfw.READ_WRITE)

try:
    # Leer registros
    n = len(tbl)
    if n > 0:
        rec0 = tbl[0]  # Primer registro
        value = rec0['FIELD_NAME']
    
    # Escribir nuevo registro
    new_rec = {
        'MARCA': 'P',
        'CODIGOP': '123',
        'FECHA': datetime.now().date(),
        'DEBE': 100.50,
    }
    tbl.append(new_rec)
    
    # Actualizar registro existente
    dbfw.write(rec0, **{'FIELD_NAME': 'new_value'})

finally:
    # SIEMPRE cerrar la tabla
    tbl.close()
```

### Modos de Apertura

- **`dbfw.READ_ONLY`**: Solo lectura
- **`dbfw.READ_WRITE`**: Lectura y escritura


### Buscar Campos (Case-Insensitive)

Para encontrar el nombre real de un campo (por si varía en mayúsculas):

```python
# Obtener lista de nombres de campos
try:
    field_names = list(getattr(tbl, 'field_names', []))
except Exception:
    field_names = []

# Buscar campo case-insensitive
fname = None
for nm in field_names:
    if str(nm).upper() == 'APUNTE':
        fname = nm
        break

# Usar el nombre real
if fname is not None:
    value = rec0[fname]
```



## Configuración del Proyecto

### Variables de Entorno (.env)

```env
# Ruta base donde se encuentran los archivos DBF
RUTA_EMPRECONTA=/ruta/a/directorio/contabilidad

# Unidad de red para traducir rutas tipo "E:\" 
# a rutas reales en el sistema
UNIDAD_CONTABILIDAD=/mnt/conta_servidor

```

### Configuración en Python (config.py)

```python
class Config:
    # Ruta donde se encuentra la DBF de empresas (EMPRESAS.DBF)
    RUTA_EMPRECONTA: str | None = os.getenv("RUTA_EMPRECONTA")
    
    # Unidad base para traducir rutas de UBICACION tipo "E:\\..." 
    # a una ruta real
    UNIDAD_CONTABILIDAD: str | None = os.getenv("UNIDAD_CONTABILIDAD")
```

---

## Gestión de Rutas y Traducción de Unidades

### Traducir Rutas de Unidades Windows a Rutas Linux/Mount

El proyecto maneja rutas que pueden venir en formato Windows (`E:\...`) y las traduce a rutas del sistema:

```python
def traducir_ruta(ubicacion, base_dir):
    """
    Traduce rutas tipo 'E:\datos\empresa' a rutas del sistema.
    
    Si UNIDAD_CONTABILIDAD está configurado, reemplaza la letra de unidad.
    """
    if re.match(r'^[A-Za-z]:[\\/]', str(ubicacion)) and config.UNIDAD_CONTABILIDAD:
        # Remover letra de unidad (E:\, D:\, etc.)
        remainder = re.sub(r'^[A-Za-z]:[\\/]', '', str(ubicacion))
        # Normalizar separadores
        remainder = remainder.replace('\\', os.sep).replace('/', os.sep)
        translated = Path(config.UNIDAD_CONTABILIDAD) / Path(remainder)
    else:
        translated = Path(base_dir) / str(ubicacion)
    
    return translated
```

### Ejemplo de Uso

```python
ubicacion = "E:\\CONTABILIDAD\\EMPRESA1"
base_dir = "/ruta/local"
unidad_contabilidad = "/mnt/servidor_conta"

# Traducir
ruta_final = traducir_ruta(ubicacion, base_dir)
# Resultado: /mnt/servidor_conta/CONTABILIDAD/EMPRESA1
```

---

## Manejo de Errores y Validaciones

### 1. Limpieza de Texto para DBF

Los archivos DBF tradicionales solo soportan ASCII. El proyecto incluye una función para limpiar caracteres especiales:

```python
def clean_text_for_dbf(text):
    """Limpia el texto para que sea compatible con DBF (ASCII)."""
    if text is None:
        return text
    
    if not isinstance(text, str):
        text = str(text)
    
    # Reemplazar caracteres problemáticos comunes
    replacements = {
        '°': 'o',
        'º': 'o',
        'ª': 'a',
        'ñ': 'n',
        'Ñ': 'N',
        'á': 'a',
        'é': 'e',
        'í': 'i',
        'ó': 'o',
        'ú': 'u',
        'Á': 'A',
        'É': 'E',
        'Í': 'I',
        'Ó': 'O',
        'Ú': 'U',
        'ü': 'u',
        'Ü': 'U',
        'ç': 'c',
        'Ç': 'C',
    }
    
    for old_char, new_char in replacements.items():
        text = text.replace(old_char, new_char)
    
    # Eliminar cualquier carácter que no sea ASCII
    try:
        text = text.encode('ascii', 'ignore').decode('ascii')
    except Exception:
        text = ''.join(char for char in text if ord(char) < 128)
    
    return text
```

### 2. Truncamiento de Campos

Los campos DBF tienen tamaño máximo definido. Se debe validar y recortar:

```python
def truncate_field(value, field_name, table):
    """Recorta un campo según el tamaño máximo definido en el DBF."""
    if value is None:
        return value
    
    # Limpiar caracteres no válidos primero
    if isinstance(value, str):
        value = clean_text_for_dbf(value)
    
    try:
        # Obtener información del campo
        field_info = table.field_info(field_name)
        if field_info and hasattr(field_info, 'length'):
            max_length = field_info.length
            if isinstance(value, str) and len(value) > max_length:
                return value[:max_length]
    except Exception:
        pass
    
    return value
```

### 3. Conversión de Tipos

```python
def conv_date(s):
    """Convierte string a objeto date para campos DBF."""
    try:
        return datetime.fromisoformat(s).date() if s else None
    except Exception:
        return None

def conv_bool(s):
    """Convierte string a booleano para campos DBF."""
    return True if str(s).upper() in ("TRUE", "T", "1", "S", "SI", "Y", "YES") else False
```

### 4. Manejo de Errores con Try-Finally

Siempre cerrar las tablas DBF después de usarlas:

```python
import dbf as dbfw

tbl = dbfw.Table(path.as_posix())
tbl.open(mode=dbfw.READ_WRITE)

try:
    # Operaciones con la tabla
    tbl.append(record)
    
    # Actualizar registro existente
    dbfw.write(record, **{'field': 'value'})

except Exception as e:
    print(f"Error operando DBF: {e}")
finally:
    # SIEMPRE cerrar
    try:
        tbl.close()
    except Exception:
        pass
```

---

## Mejores Prácticas

### 1. Elección de Librería

- **Usar `dbfread`** para:
  - Operaciones de solo lectura
  - Archivos grandes (más eficiente)
  - Análisis y consultas

- **Usar `dbf`** para:
  - Operaciones de escritura
  - Actualización de registros
  - Creación de nuevos registros

### 2. Búsqueda Case-Insensitive

Los nombres de campos y archivos pueden variar en mayúsculas. Siempre buscar case-insensitive:

```python
# Archivos
for name in ["empresas.dbf", "EMPRESAS.DBF", "Empresas.dbf"]:
    p = Path(base_dir) / name
    if p.exists():
        # encontrar
        break

# Campos
field_names = list(getattr(tbl, 'field_names', []))
fname = None
for nm in field_names:
    if str(nm).upper() == 'NOMBRE_DEL_CAMPO':
        fname = nm
        break
```

### 3. Validar Existencias

```python
if not dbf_path.exists():
    raise FileNotFoundError(f"Archivo DBF no encontrado: {dbf_path}")

if len(tbl) == 0:
    print("Tabla DBF vacía")
    return
```

### 4. Normalizar Claves

Para hacer coincidencias robustas, normalizar strings:

```python
import re

def normalizar_cif(cif):
    """Normaliza CIF para búsquedas (elimina espacios, guiones, etc.)."""
    return re.sub(r"\W", "", cif.upper())
```

### 5. Caché de Datos

Los archivos DBF raramente cambian. Implementar caché:

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def cargar_empresas():
    """Cargar empresas con caché."""
    # Tu código aquí
    return empresas_info
```

---

## Ejemplos Completos de Uso

### Ejemplo 1: Flujo Completo de Exportación de Asientos

```python
import dbf as dbfw
import dbfread
from pathlib import Path
import re
from datetime import datetime

def exportar_asientos_contables(doc_info, empresas_info, base_dir, unidad_contabilidad):
    """Exporta asientos contables a DIARIO.DBF."""
    
    # 1. Obtener datos de la empresa
    company_cif = doc_info.get('company_cif')
    ubicacion = None
    
    # Buscar en EMPRESAS.DBF
    key = re.sub(r"\W", "", company_cif.upper())
    empresa_row = empresas_info.get(key)
    
    if not empresa_row:
        raise ValueError(f"Empresa no encontrada en DBF: {company_cif}")
    
    ubicacion = empresa_row.get('UBICACION')
    
    # 2. Traducir ruta de ubicación
    if re.match(r'^[A-Za-z]:[\\/]', str(ubicacion)) and unidad_contabilidad:
        remainder = re.sub(r'^[A-Za-z]:[\\/]', '', str(ubicacion))
        remainder = remainder.replace('\\', '/')
        base_loc = Path(unidad_contabilidad) / Path(remainder)
    else:
        base_loc = Path(base_dir) / str(ubicacion)
    
    # 3. Obtener CODIGOP (carpeta contable)
    carpeta_dir = base_loc / str(doc_info['codigop'])
    if not carpeta_dir.exists():
        raise ValueError(f"Carpeta no existe: {carpeta_dir}")
    
    # 4. Leer APUNTE.DBF
    apunte_valor = leer_apunte_dbf(carpeta_dir)
    if not apunte_valor:
        raise ValueError("No se pudo leer APUNTE.DBF")
    
    apunt_doc = int(apunte_valor) + 1
    
    # 5. Escribir en DIARIO.DBF
    diario_path = carpeta_dir / "diario.dbf"
    if not diario_path.exists():
        raise ValueError(f"DIARIO.DBF no encontrado: {diario_path}")
    
    registros = [
        {
            'MARCA': 'P',
            'CODIGOP': doc_info['cuenta_gasto'],
            'FECHA': datetime.now().date(),
            'CONCEPTO': doc_info['concepto'],
            'DEBE': doc_info['total'],
            'HABER': 0,
            'APUNT': apunt_doc,
            # ... más campos
        },
        # Más registros...
    ]
    
    escribir_diario_dbf(diario_path, registros)
    
    # 6. Actualizar APUNTE.DBF
    actualizar_apunte_dbf(carpeta_dir, apunt_doc)
    
    return True

def leer_apunte_dbf(carpeta_dir):
    """Lee valor de APUNTE.DBF."""
    ap_candidates = []
    for name in ["apunte.dbf", "APUNTE.DBF", "Apunte.dbf"]:
        p = carpeta_dir / name
        if p.exists():
            ap_candidates.append(p)
    
    if not ap_candidates:
        return None
    
    t_ap = dbfw.Table(ap_candidates[0].as_posix())
    t_ap.open(mode=dbfw.READ_ONLY)
    
    try:
        if len(t_ap) > 0:
            rec0 = t_ap[0]
            field_names = list(getattr(t_ap, 'field_names', []))
            fname = None
            for nm in field_names:
                if str(nm).upper() == 'APUNTE':
                    fname = nm
                    break
            if fname:
                return str(rec0[fname]).strip()
    finally:
        t_ap.close()
    
    return None

def escribir_diario_dbf(diario_path, registros):
    """Escribe registros en DIARIO.DBF."""
    # Borrar índice
    idx_path = diario_path.with_suffix('.cdx')
    if idx_path.exists():
        idx_path.unlink()
    
    tbl = dbfw.Table(diario_path.as_posix())
    tbl.open(mode=dbfw.READ_WRITE)
    
    try:
        for registro in registros:
            # Limpiar y truncar campos
            registro_limpio = {}
            for field_name, value in registro.items():
                if isinstance(value, str):
                    value = clean_text_for_dbf(value)
                registro_limpio[field_name] = truncate_field(value, field_name, tbl)
            
            tbl.append(registro_limpio)
    finally:
        tbl.close()

def actualizar_apunte_dbf(carpeta_dir, nuevo_valor):
    """Actualiza APUNTE.DBF con nuevo valor."""
    ap_candidates = []
    for name in ["apunte.dight", "APUNTE.DBF", "Apunte.dbf"]:
        p = carpeta_dir / name
        if p.exists():
            ap_candidates.append(p)
            break
    
    if not ap_candidates:
        return False
    
    ap_path = ap_candidates[0]
    
    # Borrar índice
    ap_idx = ap_path.with_suffix('.cdx')
    if ap_idx.exists():
        ap_idx.unlink()
    
    t2 = dbfw.Table(ap_path.as_posix())
    t2.open(mode=dbfw.READ_WRITE)
    
    try:
        rec0 = t2[0]
        field_names = list(getattr(t2, 'field_names', []))
        fname = None
        for nm in field_names:
            if str(nm).strip().upper() == 'APUNTE':
                fname = nm
                break
        
        if fname:
            dbfw.write(rec0, **{fname: nuevo_valor})
            return True
    finally:
        t2.close()
    
    return False

def clean_text_for_dbf(text):
    """Limpia texto para DBF (ASCII)."""
    if text is None:
        return text
    
    if not isinstance(text, str):
        text = str(text)
    
    replacements = {
        'ñ': 'n', 'Ñ': 'N',
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    try:
        text = text.encode('ascii', 'ignore').decode('ascii')
    except Exception:
        text = ''.join(char for char in text if ord(char) < 128)
    
    return text

def truncate_field(value, field_name, table):
    """Recorta campo según tamaño máximo del DBF."""
    if value is None:
        return value
    
    if isinstance(value, str):
        value = clean_text_for_dbf(value)
    
    try:
        field_info = table.field_info(field_name)
        if field_info and hasattr(field_info, 'length'):
            max_length = field_info.length
            if isinstance(value, str) and len(value) > max_length:
                return value[:max_length]
    except Exception:
        pass
    
    return value
```



## Resumen de Puntos Clave

1. **Dos librerías**: `dbfread` (lectura) y `dbf` (lectura/escritura)
2. **Búsqueda case-insensitive**: Archivos y campos pueden variar en mayúsculas
3. **Gestión de índices**: Eliminar `.cdx` antes de escribir
4. **Cierre de tablas**: Siempre usar try-finally para cerrar tablas
5. **Limpieza de texto**: Convertir a ASCII antes de escribir
6. **Truncamiento**: Validar tamaño máximo de campos
7. **Traducción de rutas**: Manejar rutas Windows/Linux
8. **Normalización**: Normalizar claves para búsquedas
9. **Manejo de errores**: Validar existencias y manejar excepciones
10. **Caché**: Implementar caché para datos estáticos

---

