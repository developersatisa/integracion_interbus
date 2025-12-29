# ✅ Sincronización Bidireccional Completa

## 📋 Estado Actual

La sincronización bidireccional para `HolidaysAbsencesGroupATISAs` está **ACTIVA Y FUNCIONAL**.

### ¿Qué hace ahora?

✅ **COMPARA** los datos entre e03800 y Dynamics 365  
✅ **EJECUTA CAMBIOS REALES** en Dynamics 365:
  - ✅ **CREA** registros que existen en e03800 pero no en Dynamics
  - ✅ **ACTUALIZA** registros con descripciones diferentes
  - ✅ **ELIMINA** registros que existen en Dynamics pero no en e03800
✅ **SINCRONIZA** el estado final en interbus_365

> **NOTA**: La sincronización pasa a modo real. Ver `CAMBIOS_SINCRONIZACION_BIDIRECCIONAL.md` para detalles.  

## 🔍 Qué Verás en los Logs

### Registros a Eliminar

```
⚠️  REGISTRO QUE SE DEBERÍA ELIMINAR de Dynamics: [ID]
   Datos: [información del registro]
```

### Registros a Crear

```
⚠️  REGISTRO QUE SE DEBERÍA CREAR en Dynamics: [ID]
   Datos que se crearían: [estructura del registro]
```

### Registros sin Cambios

```
[numero] registros sin cambios
```

## 🚀 Ejecutar Validación

```bash
python3 main.py HolidaysAbsencesGroupATISAs
```

## 📊 Ejemplo de Output

```
============================================================
SINCRONIZACIÓN BIDIRECCIONAL (HolidaysAbsencesGroupATISAs)
============================================================
Obteniendo datos de e03800...
Obtenidos 10 registros de gruposervicios
Obteniendo datos de Dynamics 365...
Comparando datos...
e03800 tiene 10 registros
Dynamics tiene 8 registros

⚠️  REGISTRO QUE SE DEBERÍA ELIMINAR de Dynamics: ID_5
   Datos: {...}
⚠️  REGISTRO QUE SE DEBERÍA CREAR en Dynamics: ID_11
   Datos que se crearían: {...}

2 registros sin cambios

✓ Sincronización bidireccional completada
  - e03800: 10 registros
  - Dynamics antes: 8 registros
  - Dynamics después: 8 registros (sin cambios)
  - Creados: 2
  - Eliminados: 1
  - Sin cambios: 2

NOTA: MODO VALIDACIÓN - No se realizaron cambios reales en Dynamics
```

## 🔄 Activar Modo Real (Después de Validar)

Cuando estés listo para que haga cambios reales:

1. Edita `application/bidirectional_sync_use_case.py`
2. Descomenta las líneas marcadas con `# COMENTADO PARA VALIDACIÓN`
3. Comenta las líneas de log de advertencia

### Cambios a Hacer:

```python
# Línea ~136: Descomentar
self._delete_from_dynamics(entity_name, dynamics_dict[item_id], access_token)

# Línea ~149: Descomentar
self._dynamics_api.create_entity_data(entity_name, access_token, data_to_create)

# Líneas 65-71: Descomentar y ajustar
updated_dynamics_data = self._dynamics_api.get_entity_data(entity_name, access_token)
self._database_adapter.clear_entity_data(entity_name)
records_saved = self._database_adapter.save_entity_data(entity_name, updated_dynamics_data)

# Actualizar dynamics_final_count con len(updated_dynamics_data)
dynamics_final_count = len(updated_dynamics_data)

# Eliminar el campo "note"
```

## ✅ Checklist Antes de Activar Modo Real

- [ ] Verificar que los logs muestran las acciones correctas
- [ ] Confirmar que el mapeo de campos es correcto
- [ ] Verificar que el formato de DELETE funciona en Dynamics 365
- [ ] Confirmar que el formato de CREATE es correcto
- [ ] Probar con una entidad de prueba primero
- [ ] Tener backup de los datos actuales

## 🔍 Qué Validar

1. **Mapeo de IDs**: ¿Los IDs de e03800 coinciden con los de Dynamics?
2. **Campos correctos**: ¿Los campos se mapean bien (id → HolidaysAbsencesGroupId)?
3. **Formato de datos**: ¿Los datos a crear tienen el formato correcto?
4. **Operaciones**: ¿Las operaciones de DELETE/CREATE son las esperadas?

## 📞 Soporte

Si algo no se ve bien en la validación:
1. Revisa los logs detallados
2. Verifica el formato de los datos en ambos sistemas
3. Ajusta el mapeo si es necesario
4. Consulta la documentación de Dynamics 365 OData


