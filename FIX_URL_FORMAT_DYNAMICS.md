# Fix: Formato de URL para Update/Delete en Dynamics 365

## 🔍 Problema Identificado

El error original era:
```
Error actualizando registro en HolidaysAbsencesGroupATISAs: 
{"Message":"No HTTP resource was found that matches the request URI 
'https://interbus-test.sandbox.operations.eu.dynamics.com/data/HolidaysAbsencesGroupATISAs('174')'. 
No route data was found for this request."}
```

## 💡 Causa del Problema

Dynamics 365 OData requiere **claves compuestas** para las entidades que tienen `dataAreaId`. La URL incorrecta usaba solo el ID:

❌ **INCORRECTO**: `/data/HolidaysAbsencesGroupATISAs('174')`

✅ **CORRECTO**: `/data/HolidaysAbsencesGroupATISAs(dataAreaId='itb',EQMHolidaysAbsencesGroupATISAId='174')`

## 🔧 Solución Implementada

### 1. Cambios en `infrastructure/dynamics_api_adapter.py`

#### Método `update_entity_data()`:
```python
# Dynamics 365 requiere clave compuesta con dataAreaId
# Formato: /data/Entity(dataAreaId='itb',PrimaryKey='value')
key_field = 'EQMHolidaysAbsencesGroupATISAId'
url = f"/data/{entity_name}(dataAreaId='itb',{key_field}='{item_id}')"

conn.request("PATCH", url, payload, headers)
```

#### Método `delete_entity_data()`:
```python
# Dynamics 365 requiere clave compuesta con dataAreaId
# Formato: /data/Entity(dataAreaId='itb',PrimaryKey='value')
key_field = 'EQMHolidaysAbsencesGroupATISAId'
url = f"/data/{entity_name}(dataAreaId='itb',{key_field}='{item_id}')"

conn.request("DELETE", url, '', headers)
```

## 📝 Formato OData para Dynamics 365

Según la documentación de Dynamics 365 OData (https://axparadise.com/how-to-use-postman-to-access-d365fo-odata-endpoint/):

### Claves Compuestas
Para entidades con múltiples campos de clave, el formato es:
```
/data/Entity(field1='value1',field2='value2')
```

### Para HolidaysAbsencesGroupATISAs
- **Clave 1**: `dataAreaId` = `'itb'`
- **Clave 2**: `EQMHolidaysAbsencesGroupATISAId` = ID del registro

URL completa:
```
/data/HolidaysAbsencesGroupATISAs(dataAreaId='itb',EQMHolidaysAbsencesGroupATISAId='174')
```

## ⚠️ Limitación Actual

El código está **hardcodeado** para la entidad `HolidaysAbsences ath GroupATISAs`:

```python
key_field = 'EQMHolidaysAbsencesGroupATISAId'  # Campo específico
url = f"/data/{entity_name}(dataAreaId='itb',{key_field}='{item_id}')"
```

**Por qué:**
- Cada entidad de Dynamics 365 puede tener diferentes campos de clave
- Esta implementación es específica para `HolidaysAbsencesGroupATISAs`

**Si necesitas extender esto para otras entidades:**
1. Crear un diccionario de mapeo de campos de clave por entidad
2. O pasar el campo de clave como parámetro en los métodos

## ✅ Resultado Esperado

Después de este fix:

### Antes:
```
❌ PATCH /data/HolidaysAbsencesGroupATISAs('174')
   Error: No HTTP resource was found
```

### Ahora:
```
✅ PATCH /data/HolidaysAbsencesGroupATISAs(dataAreaId='itb',EQMHolidaysAbsencesGroupATISAId='174')
   ✓ Actualizado correctamente
```

## 🧪 Verificación

Para verificar que funciona:

```bash
python main.py HolidaysAbsencesGroupATISAs
```

Deberías ver en los logs:
```
🔄 ACTUALIZANDO registro en Dynamics: ID 174
   ✓ Actualizado correctamente
```

Sin errores de "No HTTP resource was found".

## 📚 Referencias

- Documentación OData de Dynamics 365: https://axparadise.com/how-to-use-postman-to-access-d365fo-odata-endpoint/
- Microsoft Learn: Dynamics 365 Finance and Operations OData

## 🔄 Próximos Pasos

Si necesitas aplicar sincronización bidireccional a otras entidades:

1. **Identificar campos de clave** de la nueva entidad
2. **Actualizar el adaptador** para soportar múltiples esquemas de clave
3. **O crear adaptadores específicos** para cada entidad

Ejemplo para extensión futura:
```python
# Configuración de campos de clave por entidad
ENTITY_KEYS = {
    'HolidaysAbsencesGroupATISAs': {
        'primary_key': 'EQMHolidaysAbsencesGroupATISAId',
        'data_area_id': 'itb'
    },
    # Agregar más entidades aquí...
}
```

