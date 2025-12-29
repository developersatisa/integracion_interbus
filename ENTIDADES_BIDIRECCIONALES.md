# Entidades con Sincronización Bidireccional

## 📋 Entidades Soportadas

Actualmente se implementa sincronización bidireccional completa para las siguientes entidades:

1. **HolidaysAbsencesGroupATISAs** - Grupos de Vacaciones y Ausencias
2. **IncidentGroupATISAs** - Grupos de Incidentes
3. **AdvanceGroupATISAs** - Grupos de Avances
4. **LibrariesGroupATISAs** - Grupos de Bibliotecas
5. **LeaveGroupATISAs** - Grupos de Licencias

## 🔄 Mapeo de Datos

### HolidaysAbsencesGroupATISAs
- **Origen e03800**: `gruposervicios` WHERE `id_servicios = 30`
- **Destino Dynamics**: Entidad `HolidaysAbsencesGroupATISAs`
- **Campo clave Dynamics**: `EQMHolidaysAbsencesGroupATISAId`
- **Campo descripción**: `Description`

### IncidentGroupATISAs
- **Origen e03800**: `gruposervicios` WHERE `id_servicios = 10`
- **Destino Dynamics**: Entidad `IncidentGroupATISAs`
- **Campo clave Dynamics**: `EQMIncidentGroupATISAId`
- **Campo descripción**: `Description`

### AdvanceGroupATISAs
- **Origen e03800**: `gruposervicios` WHERE `id_servicios = 20`
- **Destino Dynamics**: Entidad `AdvanceGroupATISAs`
- **Campo clave Dynamics**: `EQMAdvanceGroupATISAId`
- **Campo descripción**: `Description`

### LibrariesGroupATISAs
- **Origen e03800**: `gruposervicios` WHERE `id_servicios = 80`
- **Destino Dynamics**: Entidad `LibrariesGroupATISAs`
- **Campo clave Dynamics**: `EQMLibrariesGroupATISAId`
- **Campo descripción**: `Description`

### LeaveGroupATISAs
- **Origen e03800**: `gruposervicios` WHERE `id_servicios = 100`
- **Destino Dynamics**: Entidad `LeaveGroupATISAs`
- **Campo clave Dynamics**: `EQMLeaveGroupATISAId`
- **Campo descripción**: `Description`

## 📊 Estructura de Datos

### Tabla e03800.gruposervicios
```sql
SELECT id, nombre
FROM gruposervicios
WHERE id_servicios IN (10, 20, 30, 80, 100)
```

**Campos**:
- `id`: Identificador único del grupo
- `nombre`: Descripción del grupo
- `id_servicios`: Tipo de servicio
  - 10 = Incidencias
  - 20 = Avances
  - 30 = Vacaciones y Ausencias
  - 80 = Bibliotecas
  - 100 = Licencias

### Dynamics 365
**Campos comunes**:
- `dataAreaId`: Siempre "itb"
- Campo ID específico según entidad
- `Description`: Descripción del grupo

## 🚀 Uso

### Sincronizar una entidad específica
```bash
python main.py HolidaysAbsencesGroupATISAs
python main.py IncidentGroupATISAs
```

### Sincronizar todas las entidades (incluye bidireccionales)
```bash
python main.py
```

## 🔧 Operaciones Realizadas

Para ambas entidades, la sincronización realiza:

1. **CREATE**: Crea registros que existen en e03800 pero no en Dynamics
2. **UPDATE**: Actualiza registros con descripciones diferentes
3. **DELETE**: Elimina registros que existen en Dynamics pero no en e03800
4. **SINCRONIZACIÓN BD**: Guarda el estado final en `interbus_365.dynamic_entities`

## 📝 Ejemplo de Salida

```
============================================================
SINCRONIZACIÓN BIDIRECCIONAL (IncidentGroupATISAs)
============================================================
Obteniendo datos de e03800...
Obtenidos 15 registros de gruposervicios (id_servicios=10)
Obteniendo datos de Dynamics 365...

🔄 ACTUALIZANDO registro en Dynamics: ID 25
   ✓ Actualizado correctamente

➕ CREANDO registro en Dynamics: ID 30
   ✓ Creado correctamente

✓ IncidentGroupATISAs: Sincronización bidireccional completada
  - e03800: 15 registros
  - Dynamics antes: 13 registros
  - Dynamics después: 15 registros
  - Creados: 2
  - Eliminados: 0
  - Sin cambios: 13
```

## 🔍 Consideraciones Técnicas

### Campos de Clave
Cada entidad tiene su propio campo de clave primaria en Dynamics:
- HolidaysAbsencesGroupATISAs: `EQMHolidaysAbsencesGroupATISAId`
- IncidentGroupATISAs: `EQMIncidentGroupATISAId`
- AdvanceGroupATISAs: `EQMAdvanceGroupATISAId`
- LibrariesGroupATISAs: `EQMLibrariesGroupATISAId`
- LeaveGroupATISAs: `EQMLeaveGroupATISAId`

Esto se maneja automáticamente en el código mediante el método centralizado `_get_primary_field()`.

### URLs de API
Las operaciones UPDATE/DELETE usan formato de clave compuesta:
```
PATCH /data/IncidentGroupATISAs(dataAreaId='itb',EQMIncidentGroupATISAId='25')
DELETE /data/IncidentGroupATISAs(dataAreaId='itb',EQMIncidentGroupATISAId='25')
```

## ✅ Verificación

### Verificar en Dynamics 365
1. Acceder a la entidad correspondiente
2. Verificar que los registros coincidan con e03800
3. Comparar IDs y descripciones

### Verificar en Base de Datos
```sql
SELECT * 
FROM dynamic_entities 
WHERE entity_name IN ('HolidaysAbsencesGroupATISAs', 'IncidentGroupATISAs', 'AdvanceGroupATISAs', 'LibrariesGroupATISAs', 'LeaveGroupATISAs');
```

## 🔄 Extender a Otras Entidades

Para agregar más entidades con sincronización bidireccional:

1. **Actualizar mapeo de servicio** en `execute()`:
   ```python
   service_id = 10 if entity_name == 'IncidentGroupATISAs' else ...
   ```

2. **Agregar campo clave** en `_extract_data_area_id_from_dynamics()`:
   ```python
   elif entity_name == 'NuevaEntidad':
       primary_field = 'EQMNuevaEntidadId'
   ```

3. **Actualizar creación** en `_compare_and_sync()`:
   ```python
   elif entity_name == 'NuevaEntidad':
       data_to_create = {
           "dataAreaId": "itb",
           "EQMNuevaEntidadId": item_id,
           "Description": item_nombre
       }
   ```

4. **Agregar a lista bidireccional** en `main.py`:
   ```python
   BIDIRECTIONAL_ENTITIES = ['HolidaysAbsencesGroupATISAs', 'IncidentGroupATISAs', 'NuevaEntidad']
   ```

## 📞 Archivos Relacionados

- `application/bidirectional_sync_use_case.py` - Lógica de sincronización
- `infrastructure/dynamics_api_adapter.py` - Operaciones de API
- `infrastructure/e03800_database_adapter.py` - Acceso a e03800
- `main.py` - Orquestación principal

## 🎯 Estado Actual

✅ **HolidaysAbsencesGroupATISAs**: Completamente funcional
✅ **IncidentGroupATISAs**: Completamente funcional
✅ **AdvanceGroupATISAs**: Completamente funcional
✅ **LibrariesGroupATISAs**: Completamente funcional
✅ **LeaveGroupATISAs**: Completamente funcional

Todas las entidades ejecutan sincronización bidireccional completa contra Dynamics 365.

