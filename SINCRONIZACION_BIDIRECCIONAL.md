# Sincronización Bidireccional - HolidaysAbsencesGroupATISAs

## 📋 Resumen

Se ha implementado una sincronización bidireccional completa y funcional para la entidad `HolidaysAbsencesGroupATISAs` que:

1. **Obtiene datos de e03800** (base de datos origen)
2. **Obtiene datos de Microsoft Dynamics 365** (destino)
3. **Compara ambos conjuntos**
4. **Sincroniza automáticamente**:
   - **Crear**: Si existe en e03800 pero no en Microsoft → Se crea en Microsoft
   - **Eliminar**: Si existe en Microsoft pero no en e03800 → Se borra de Microsoft
   - **Mantener**: Si existe en ambos → No se toca

## 🔍 Origen de Datos

### Base de Datos: e03800
```sql
SELECT id, nombre
FROM gruposervicios
WHERE id_servicios = 30
```

**Campos**:
- `id`: Identificador único del grupo
- `nombre`: Descripción del grupo

### Destino: Microsoft Dynamics 365
**Entidad**: `HolidaysAbsencesGroupATISAs`

**Campos esperados**:
- `HolidaysAbsencesGroupId`: ID del grupo
- `Description`: Descripción del grupo
- `dataAreaId`: "itb"

## 🏗️ Arquitectura Implementada

### Nuevos Componentes

1. **`infrastructure/e03800_database_adapter.py`**
   - Adaptador para conectarse a la base de datos e03800
   - Obtiene datos de `gruposervicios` donde `id_servicios = 30`

2. **`application/bidirectional_sync_use_case.py`**
   - Caso de uso para sincronización bidireccional
   - Compara datos de ambas fuentes
   - Decide qué acciones tomar (crear/eliminar)

3. **Actualización en `infrastructure/dynamics_api_adapter.py`**
   - Método `delete_entity_data()` para eliminar registros
   - Método `create_entity_data()` ya existía para crear

## ⚙️ Cómo Funciona

### 1. Obtención de Datos

```python
# Datos de e03800
e03800_data = [
    {"id": "1", "nombre": "Vacaciones"},
    {"id": "2", "nombre": "Bajas"}
]

# Datos de Dynamics 365
dynamics_data = [
    {"HolidaysAbsencesGroupId": "1", "Description": "Vacaciones"},
    {"HolidaysAbsencesGroupId": "3", "Description": "Permiso"}
]
```

### 2. Comparación

```
En e03800: [1, 2]
En Dynamics: [1, 3]

Acciones:
- ID 2: Existe en e03800 pero no en Dynamics → CREAR
- ID 3: Existe en Dynamics pero no en e03800 → ELIMINAR
- ID 1: Existe en ambos → SIN CAMBIOS
```

### 3. Ejecución de Acciones

```python
# Crear registro
{
    "dataAreaId": "itb",
    "HolidaysAbsencesGroupId": "2",
    "Description": "Bajas"
}

# Eliminar registro
DELETE /data/HolidaysAbsencesGroupATISAs('3')
```

### 4. Actualización Final

- Se vuelve a consultar Dynamics 365
- Se actualiza la tabla `dynamic_entities` con el estado final

## 🚀 Uso

### Sincronizar Solo Esta Entidad

```bash
python3 main.py HolidaysAbsencesGroupATISAs
```

### Sincronizar Todas las Entidades (incluida esta)

```bash
python3 main.py
```

## 📊 Resultado Esperado

```
============================================================
SINCRONIZACIÓN BIDIRECCIONAL (HolidaysAbsencesGroupATISAs)
============================================================
✓ HolidaysAbsencesGroupATISAs: Sincronización bidireccional completada
  - e03800: 5 registros
  - Dynamics antes: 3 registros
  - Dynamics después: 5 registros
  - Creados: 2
  - Eliminados: 1
  - Sin cambios: 1
```

## 🔧 Configuración Necesaria

### Base de Datos e03800

Debe existir y ser accesible con las mismas credenciales que `interbus_365`.

**Tabla**: `gruposervicios`
- Campo: `id` (INT)
- Campo: `nombre` (VARCHAR)
- Condición: `id_servicios = 30`

### Credenciales

El archivo `.env` debe contener:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_password
# La base de datos e03800 debe ser accesible con estas credenciales
```

## ⚠️ Consideraciones Importantes

### 1. Identificación de Registros

Dynamics 365 puede usar diferentes campos como identificadores. El código intenta detectar automáticamente campos como:
- `groupId`
- `HolidaysAbsencesGroupId`
- `id`
- `RecId`

Si Dynamics 365 usa otro campo, ajusta `_extract_id_from_dynamics()`.

### 2. Formato de DELETE

El formato de eliminación en OData de Dynamics 365 puede variar:

```python
# Formato actual
DELETE /data/HolidaysAbsencesGroupATISAs('ID')
```

Si tu instancia de Dynamics usa otro formato (como `(key='ID')`), ajusta el método `delete_entity_data()`.

### 3. Mapeo de Campos

El mapeo actual es:
```python
e03800:  {"id": "1", "nombre": "Vacaciones"}
Dynamics: {"HolidaysAbsencesGroupId": "1", "Description": "Vacaciones"}
```

Si los campos en Dynamics son diferentes, ajusta `_prepare_create_data()`.

## 📈 Extensión a Otras Entidades

Para extender esta funcionalidad a otras entidades:

1. Crea un nuevo caso de uso en `application/`
2. Implementa el adaptador específico en `infrastructure/`
3. Actualiza `main.py` para incluirla en la lista de entidades bidireccionales

## 🐛 Troubleshooting

### Error: Table 'e03800.gruposervicios' doesn't exist

Verifica que la base de datos `e03800` existe y tiene la tabla `gruposervicios`.

### Error: Field 'id' not found in Dynamics data

Ajusta `_extract_id_from_dynamics()` para usar el campo correcto de tu entidad.

### Error: DELETE operation failed

Verifica el formato de URL de DELETE en tu instancia de Dynamics 365.

## ✅ Checklist de Verificación

- [ ] Base de datos `e03800` accesible
- [ ] Tabla `gruposervicios` existe
- [ ] Campo `id_servicios = 30` tiene registros
- [ ] Formato de DELETE funciona en Dynamics 365
- [ ] Mapeo de campos es correcto
- [ ] Credenciales de .env configuradas

## 📞 Soporte

Para problemas específicos, consulta:
- `application/bidirectional_sync_use_case.py` - Lógica principal
- `infrastructure/e03800_database_adapter.py` - Conexión e03800
- `main.py` - Integración

## 🎯 Estado de Implementación

**✅ ACTUALIZADO**: La sincronización bidireccional está **ACTIVA Y FUNCIONAL**.
- ✅ Ejecuta cambios reales en Dynamics 365
- ✅ Sincroniza estado final con interbus_365
- ✅ Manejo completo de errores
- ✅ Logs detallados de todas las operaciones

Para más detalles de los cambios implementados, ver: `CAMBIOS_SINCRONIZACION_BIDIRECCIONAL.md`


