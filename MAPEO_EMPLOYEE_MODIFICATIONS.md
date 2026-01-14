# Mapeo de Campos: EmployeeModifications → com_altas

Este documento mapea los campos del endpoint `EmployeeModifications` de Dynamics 365 a los campos de la tabla `com_altas` en la base de datos e03800.

## Estructura de la Tabla de Referencia: `dfo_com_altas`

La tabla `dfo_com_altas` almacena la relación entre los registros de `com_altas` y los ETags de Dynamics 365:

```sql
CREATE TABLE IF NOT EXISTS `dfo_com_altas` (
  `id` INT(10) UNSIGNED NOT NULL PRIMARY KEY COMMENT 'ID de com_altas (referencia directa, sin codificar)',
  `etag` VARCHAR(255) NOT NULL COMMENT 'Valor de @odata.etag del endpoint codificado en base64 (tiene caracteres especiales)',
  `personnel_number` VARCHAR(50) DEFAULT NULL COMMENT 'PersonnelNumber del endpoint (para referencia rápida)',
  `created_date` DATETIME NOT NULL COMMENT 'CreatedDate del endpoint EmployeeModifications (para validación de orden cronológico)',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación del registro en esta tabla',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Fecha de actualización del registro',
  INDEX `idx_etag` (`etag`),
  INDEX `idx_personnel_number` (`personnel_number`),
  INDEX `idx_created_date` (`created_date`) COMMENT 'Índice para validación de orden cronológico',
  UNIQUE KEY `uk_etag` (`etag`) COMMENT 'Garantiza que cada ETag solo se procese una vez',
  FOREIGN KEY (`id`) REFERENCES `com_altas`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Importante:**
- El `id` es INT directo (sin codificar) para referencias eficientes a `com_altas.id`
- El `etag` se codifica en base64 porque contiene caracteres especiales (ej: `W/\"JzEsNTYzNzE0NDU3OCc=\"`)

## Mapeo de Campos

| Campo Endpoint (EmployeeModifications) | Tipo | Campo com_altas | Tipo | Estado | Notas |
|----------------------------------------|------|-----------------|------|--------|-------|
| `@odata.etag` | string | - | - | ✅ | Se guarda en `dfo_com_altas.etag` (codificado en base64) |
| `CompanyIdATISA` | string | `codiemp` | char(5) | ✅ | Código de empresa |
| `Gender` | string/null | `sexo` | char(100) | ✅ | Género del empleado |
| `LastName1` | string | `apellido1` | char(20) | ✅ | Primer apellido |
| `LastName2` | string | `apellido2` | char(20) | ✅ | Segundo apellido |
| `HolidaysAbsencesGroupATISAId` | string | `grupo_vacaciones` | int(10) | ✅ | Grupo de vacaciones (convertir string a int) |
| `Salary` | string | `salario` | decimal(14,4) | ✅ | Salario (convertir string a decimal) |
| `BankAccount` | string | `ccc` | char(41) | ✅ | Cuenta bancaria / CCC |
| `StartDate` | datetime | `fechaalta` | date | ✅ | Fecha de alta (extraer solo fecha de datetime) |
| `LibrariesGroupATISAId` | string | `grupo_biblioteca` | int(10) | ✅ | Grupo de biblioteca (convertir string a int) |
| `AdvanceGroupATISAId` | string | `grupo_anticipos` | int(10) | ✅ | Grupo de anticipos (convertir string a int) |
| `NASS` | string | `naf` | char(12) | ✅ | Número de afiliación a la seguridad social (trabajadores.numeross) |
| `BirthDate` | datetime | `fechanacimiento` | date | ✅ | Fecha de nacimiento (extraer solo fecha de datetime) |
| `Email` | string | `email` | varchar(120) | ✅ | Correo electrónico |
| `Phone` | string | `telefono` | char(13) | ✅ | Teléfono |
| `FirstName` | string | `nombre` | char(15) | ✅ | Nombre del empleado |
| `ZipCode` | string | `cpostal` | char(5) | ✅ | Código postal |
| `CreatedDate` | datetime | - | - | ❌ | No se integra de momento |
| `PersonnelNumber` | string | `nummat` | varchar(10) | ✅ | Número de matrícula (trabajadores.nummat) |
| `CompanyId` | string | - | - | ❌ | No se integra de momento |
| `EndDate` | datetime | `fechafincontrato` | date | ✅ | Fecha fin contrato (extraer solo fecha de datetime) |  
| `SeniorityDate` | datetime | `fecha_antig` | char(100) | ✅ | Fecha antiguedad (extraer solo fecha de datetime) |
| `educationlevel` | string | - | - | ❌ | No se integra de momento |
| `VacationSettlement` | string | - | - | ❌ | No se integra de momento |
| `DailySchedule` | number | - | - | ❌ | No se integra de momento |
| `HighsLowsChangesID` | string | - | - | ❌ | No se integra de momento |
| `Street` | string | `domicilio` | char(60) | ✅ | Dirección |
| `CNAEOccupationCode` | string | - | - | ❌ | No se integra de momento |
| `JobPositionIdATISA` | string | `puesto` | varchar(120) | ✅ | Lookup en `lista_puestos` por `codiemp` y `concepto LIKE` (com_altas guarda `codiemp-codpuesto`) |
| `TransitionReasonDescription` | string | - | - | ❌ | No se integra de momento |
| `AmountKmID` | string | - | - | ❌ | No se integra de momento |
| `QuotationGroupATISAId` | string | - | - | ❌ | No se integra de momento |
| `VATNum` | string | `nif` | char(14) | ✅ | DNI/NIF (obligatorio) |
| `DisabilityPercentage` | number | - | - | ❌ | No se integra de momento |
| `Department` | string | - | - | ❌ | No se integra de momento |   
| `TestingPeriodId` | string | - | - | ❌ | No se integra de momento |
| `CCC` | string | - | - | ❌ | No se integra de momento |   //codigo cuenta cotizacion
| `Observations` | string | - | - | ❌ | No se integra de momento |
| `SubPosition` | string | `subpuesto` | varchar(120) | ✅ | Lookup en `lista_subpuestos` (com_altas guarda `codpuesto`) |
| `IncidentGroupATISAId` | string | - | - | ❌ | No se integra de momento |
| `County` | string | `provincia` | char(30) | ✅ | Si llega como ID numerico, se resuelve en `provincias_integracion.descripcion` |
| `LeaveGroupATISAId` | string | - | - | ❌ | No se integra de momento |
| `NationalityCountryRegion` | string/null | `nacionalidad` | int(10) | ✅ | Se busca en `acceso.paises` (pais -> codpais) |
| `City` | string | `localidad` | char(30) | ✅ | Ciudad |
| `VacationCalenderId` | string | - | - | ❌ | No se integra de momento |  
| `Reasonforcontract` | string | `motivo_contrato` | text | ✅ | Motivo de contrato |
| `BenefitEmploymentCategoryId` | string | - | - | ❌ | No se integra de momento |
| `CountryRegionId` | string | - | - | ❌ | No se integra (Supabase devuelve int y en BD se maneja string) |
| `Processed` | string | - | - | ❌ | No se integra de momento |    //una vez procesado por atisa
| `WorkerPlaceID` | string | - | - | ❌ | No se integra de momento |    //que significa categoria puesto o puesto2
| `ContractTypeID` | string | `tipo_contrato` | char(3) | ✅ | Tipo de contrato |
| `Mobilephone` | string | `telmovil` | int(13) | ✅ | Teléfono móvil |
| `VacationBalanceId` | string | - | - | ❌ | No se integra de momento |

## Campos de com_altas (para referencia)

| Campo com_altas | Tipo | Descripción |
|-----------------|------|-------------|
| `id` | int(10) unsigned | ID autoincremental (referencia directa en dfo_com_altas, sin codificar) |
| `codiemp` | char(5) | Código de empresa |
| `codicen` | char(3) | Código de centro |
| `coditraba` | char(5) | Código de trabajador |
| `tipo` | char(2) | Tipo |
| `nombre` | char(15) | Nombre |
| `apellido1` | char(20) | Primer apellido |
| `apellido2` | char(20) | Segundo apellido |
| `nif` | char(14) | NIF |
| `naf` | char(12) | NAF |
| `fechanacimiento` | date | Fecha de nacimiento |
| `mod145` | varchar(255) | Mod 145 |
| `mod145_nombre` | varchar(255) | Nombre Mod 145 |
| `mime_mod145` | varchar(120) | MIME Mod 145 |
| `complementario` | varchar(255) | Complementario |
| `complementario_nombre` | varchar(255) | Nombre complementario |
| `mime_complementario` | varchar(120) | MIME complementario |
| `titulacion` | char(2) | Titulación |
| `domicilio` | char(60) | Domicilio |
| `localidad` | char(30) | Localidad |
| `provincia` | char(30) | Provincia |
| `cpostal` | char(5) | Código postal |
| `nacionalidad` | int(10) | Nacionalidad |
| `email` | varchar(120) | Email |
| `telefono` | char(13) | Teléfono |
| `fechaalta` | date | Fecha de alta |
| `tipo_contrato` | char(3) | Tipo de contrato |
| `contrato_temporal` | tinyint(1) | Contrato temporal |
| `fechafincontrato` | date | Fecha fin contrato |
| `motivo_contrato` | text | Motivo de contrato |
| `interinidad` | tinyint(1) | Interinidad |
| `persona_sustitucion` | varchar(120) | Persona sustitución |
| `motivo_sustitucion` | text | Motivo sustitución |
| `categoria_puesto` | varchar(120) | Categoría puesto |
| `horas_semana` | decimal(6,4) | Horas semana |
| `distribucion_horas` | text | Distribución horas |
| `grupo_cotizacion` | char(2) | Grupo cotización |
| `situacion_cotizacion` | char(1) | Situación cotización |
| `uds_organizativas` | varchar(50) | UDs organizativas |
| `sexo` | char(100) | Sexo |
| `estado_civil` | char(100) | Estado civil |
| `fecha_antig` | char(100) | Fecha antigüedad |
| `ultimo_gestor` | varchar(64) | Último gestor |
| `fecha_procesando` | datetime | Fecha procesando |
| `fecha_ss` | datetime | Fecha SS |
| `fecha_finalizado` | datetime | Fecha finalizado |
| `token` | varchar(32) | Token |
| `grupo_altas` | int(10) | Grupo altas |
| `salario` | decimal(14,4) | Salario |
| `ccc` | char(41) | CCC |
| `codidepa` | char(30) | Código departamento |
| `tienda` | char(30) | Tienda |
| `grupo_anticipos` | int(10) | Grupo anticipos |
| `grupo_incidencias` | int(10) | Grupo incidencias |
| `grupo_vacaciones` | int(10) | Grupo vacaciones |
| `grupo_biblioteca` | int(10) | Grupo biblioteca |
| `grupo_planning` | int(10) | Grupo planning |
| `grupo_ficha` | int(10) | Grupo ficha |
| `grupo_bajas` | int(10) | Grupo bajas |
| `grupo_adicional_90` | int(10) | Grupo adicional 90 |
| `calendario` | int(10) | Calendario |
| `rol_empleado` | int(10) | Rol empleado |
| `fechasolicitud` | timestamp | Fecha solicitud |
| `estado` | char(2) | Estado |
| `id_usuario` | int(10) | ID usuario |
| `observa` | text | Observaciones |
| `observa_admin` | text | Observaciones admin |
| `observa_atisa` | text | Observaciones ATISA |
| `generico1` a `generico20` | text | Campos genéricos |
| `motivo_baja` | varchar(50) | Motivo baja |
| `nombre_agente_atisa` | varchar(120) | Nombre agente ATISA |
| `id_usuario_adm` | int(10) | ID usuario admin |
| `l_importado` | tinyint(1) | Importado |
| `fechaimportado` | datetime | Fecha importado |
| `telefono2` | int(13) | Teléfono 2 |
| `nummat` | varchar(10) | Número matrícula |
| `telmovil` | int(13) | Teléfono móvil |
| `puesto` | varchar(120) | Puesto |
| `subpuesto` | varchar(120) | Subpuesto |
| `nivel` | varchar(120) | Nivel |
| `vac_pendientes` | decimal(5,2) | Vacaciones pendientes |
| `tipo_vac_pendientes` | varchar(55) | Tipo vacaciones pendientes |
| `just_cuentabancaria` | varchar(255) | Justificación cuenta bancaria |
| `gestionar_alta_rpa` | int(1) | Gestionar alta RPA |
| `gestionada_alta_rpa` | int(1) | Gestionada alta RPA |
| `num_pagas` | int(2) | Número pagas |
| `observaciones_modcon` | text | Observaciones modificación contrato |
| `tipo_modcon` | varchar(50) | Tipo modificación contrato |
| `duracion_modcon` | int(1) | Duración modificación contrato |
| `dias_semana_modcon` | int(1) | Días semana modificación contrato |
| `forma_modcon` | varchar(10) | Forma modificación contrato |
| `parcialidad_modcon` | decimal(7,4) | Parcialidad modificación contrato |
| `op_modcon` | varchar(50) | OP modificación contrato |
| `fecha_modcon` | date | Fecha modificación contrato |
| `distribucion_modcon` | text | Distribución modificación contrato |
| `dias_modcon` | int(2) | Días modificación contrato |
| `meses_modcon` | int(2) | Meses modificación contrato |
| `tipo_modificacion_modcon` | int(11) | Tipo modificación modificación contrato |
| `fecharealizacion` | date | Fecha realización |
| `fecha_permiso_residencia` | date | Fecha permiso residencia |
| `residencia_permanente` | int(1) | Residencia permanente |
| `horas_anuales` | decimal(6,2) | Horas anuales |

## Leyenda de Estados

- ✅ **Mapeado**: Campo ya mapeado y se integrará en com_altas
- ❌ **No se integra**: Campo que no se integrará de momento

## Notas de Implementación

1. **Codificación Base64 del ETag**: El `@odata.etag` contiene caracteres especiales (ej: `W/\"JzEsNTYzNzE0NDU3OCc=\"`) que pueden causar problemas en la base de datos, por lo que se codifica en base64 antes de guardarlo
   - Ejemplo: `etag = "W/\"JzEsNTYzNzE0NDU3OCc=\""` → `base64 = "Vy9cIkp6RXM1Tll6TXpNNEU1NzhjXCc9XCI="`
   - El `id` de `com_altas` se guarda como INT directo (sin codificar) para referencias eficientes

2. **Tabla dfo_com_altas**: Relación entre ETag y ID de com_altas
   - `id`: INT UNSIGNED - referencia directa al `id` de `com_altas` (sin codificar, para eficiencia)
   - `etag`: VARCHAR - valor del `@odata.etag` codificado en base64
   - `created_date`: DATETIME - `CreatedDate` del endpoint (para validación de orden cronológico)
   - `personnel_number`: VARCHAR - `PersonnelNumber` del endpoint (opcional, para referencia rápida)
   - Permite rastrear qué registros de Dynamics 365 ya han sido procesados
   - Evita duplicados al sincronizar
   - Permite validar orden cronológico de solicitudes
   - FOREIGN KEY garantiza integridad referencial

3. **Proceso de Sincronización**:
   - Obtener datos de `EmployeeModifications`
   - **FASE 1 (Implementación inicial)**: Procesar solo el primer registro
   - **FASE 2**: Procesar los primeros 2 registros
   - **FASE 3**: Procesar los primeros 3 registros
   - **FASE FINAL**: Procesar todos los registros
   
   - Para cada registro procesado:
     
     **PASO 1: Verificación de ETag (PRIORITARIO)**
     - Codificar el `@odata.etag` en base64
     - Verificar si el ETag (codificado) ya existe en `dfo_com_altas` (base de datos `interbus_365`)
     - **Si el ETag YA existe**: 
       - El registro ya fue procesado anteriormente
       - **Acción**: **OMITIR** el registro (no procesar, pasar al siguiente)
       - **Razón**: Evita duplicados y reprocesamiento
     
     - **Si el ETag NO existe**:
       - El registro es nuevo y necesita ser validado
       - Continuar con **PASO 2: Identificación de tipo** (ver lógica de negocio abajo)
     
    **PASO 2: Identificación de tipo (ALTA vs MODIFICACIÓN)**
    - Aplicar la lógica de negocio (CASO 1, CASO 2.A, CASO 2.B, etc.)
    - Determinar si es ALTA o MODIFICACIÓN
    - Validar que `VATNum` exista (DNI/NIF obligatorio)
    - Si es OMITIR (solicitud antigua), no crear registro
     
     **PASO 3: Validación de orden cronológico (antes de insertar)**
     - **IMPORTANTE**: La validación es específica por tipo (ALTA o MODIFICACIÓN)
     - **IMPORTANTE**: Las bases de datos están en el mismo servidor, se pueden hacer consultas cruzadas usando `interbus_365.dfo_com_altas` y `e03800.com_altas`
     
     - **Si el registro es ALTA (`tipo = 'A'`)**:
       - Verificar que el `CreatedDate` del registro actual sea **mayor** al último `CreatedDate` de un registro ALTA (`tipo = 'A'`) del mismo trabajador
       - **Consulta SQL**:
         ```sql
         SELECT MAX(dfo.created_date) 
         FROM interbus_365.dfo_com_altas dfo
         JOIN e03800.com_altas ca ON dfo.id = ca.id
         WHERE ca.nombre = 'dato_endpoint'
           AND ca.apellido1 = 'dato_endpoint'
           AND ca.apellido2 = 'dato_endpoint'
           AND ca.codiemp = 'dato_endpoint'
           AND ca.tipo = 'A'
         ```
       - **Si `CreatedDate` <= último `created_date` de ALTA**: 
         - **Acción**: **OMITIR** el registro (no procesar, es un alta fuera de orden)
       - **Si `CreatedDate` > último `created_date` de ALTA** o no hay altas previas (resultado NULL):
         - Continuar con PASO 4
     
     - **Si el registro es MODIFICACIÓN (`tipo = 'M'`)**:
       - Verificar que el `CreatedDate` del registro actual sea **mayor** al último `CreatedDate` de un registro MODIFICACIÓN (`tipo = 'M'`) del mismo trabajador
       - **Consulta SQL** (incluye filtro por `coditraba` del trabajador activo):
         ```sql
         SELECT MAX(dfo.created_date) 
         FROM interbus_365.dfo_com_altas dfo
         JOIN e03800.com_altas ca ON dfo.id = ca.id
         WHERE ca.nombre = 'dato_endpoint'
           AND ca.apellido1 = 'dato_endpoint'
           AND ca.apellido2 = 'dato_endpoint'
           AND ca.codiemp = 'dato_endpoint'
           AND ca.tipo = 'M'
           AND ca.coditraba = 'coditraba_del_trabajador_activo'
         ```
       - **Si `CreatedDate` <= último `created_date` de MODIFICACIÓN**: 
         - **Acción**: **OMITIR** el registro (no procesar, es una modificación fuera de orden)
       - **Si `CreatedDate` > último `created_date` de MODIFICACIÓN** o no hay modificaciones previas (resultado NULL):
         - Continuar con PASO 4
     
     - **Razón**: Mantener integridad cronológica independiente para altas y modificaciones
     
     **PASO 4: Asignación de `coditraba` según tipo**
     - **Si es ALTA (`tipo = 'A'`)**:
       - `coditraba` en `com_altas` = **0** (cero)
       - **Razón**: Es un nuevo trabajador, aún no tiene código asignado
     
     - **Si es MODIFICACIÓN (`tipo = 'M'`)**:
       - Obtener `coditraba` del trabajador activo en la tabla `trabajadores` (base de datos `e03800`)
       - `coditraba` en `com_altas` = `coditraba` del trabajador activo
       - **Razón**: Es una modificación de un trabajador existente, mantener su código
     
    **PASO 5: Creación de registros**
    - **IMPORTANTE**: Primero crear en `com_altas` para obtener el `id`, y finalmente crear en `dfo_com_altas`
     - **Paso 5.1**: Crear registro en `com_altas` (base de datos `e03800`) con los datos mapeados:
       - Incluir `tipo` ('A' o 'M')
       - Incluir `coditraba` (0 para altas, código del trabajador para modificaciones)
       - Incluir todos los demás campos mapeados
       - **Campos no mapeados**: Se insertan como `NULL`
       - **Valores NULL o vacíos del endpoint**: Se insertan como `NULL` en la base de datos
       - **Conversiones fallidas** (string no numérico, fecha inválida): Se insertan como `NULL`
    - **Paso 5.2**: Obtener el `id` autoincremental generado de `com_altas`
    - **Paso 5.3**: Guardar relación en `dfo_com_altas` (base de datos `interbus_365`):
      - `id`: INT directo (referencia a `com_altas.id` obtenido en paso 5.2)
      - `etag`: VARCHAR con el ETag codificado en base64
      - `personnel_number`: VARCHAR con el `PersonnelNumber` (opcional, para referencia)
      - `created_date`: DATETIME con el `CreatedDate` del endpoint (para validación cronológica)

## Sincronización Manual de `trabajadores` desde `com_altas`

Existe un script separado para crear registros en `trabajadores` a partir de `com_altas` (solo `tipo = 'A'`).
El flujo **no** se ejecuta durante la sincronización normal de EmployeeModifications.

```bash
python scripts/sync_trabajadores_from_com_altas.py
```

- Lee `com_altas` con `tipo = 'A'`.
- Verifica si el trabajador ya existe en `trabajadores` (por `codiemp`, `nombre`, `apellido1`, `apellido2`, y NIF/DNI si existe).
- Si no existe, lo crea en `trabajadores`.

## Lógica de Negocio: Identificación de Altas vs Modificaciones

**IMPORTANTE**: Esta lógica solo se aplica si el ETag NO existe en `dfo_com_altas` (ver PASO 1 del proceso de sincronización).

### Campos de Identificación del Trabajador

Para identificar a qué trabajador pertenece un registro del endpoint, se usan los siguientes campos:
- `CompanyIdATISA` → `codiemp` (código de empresa)
- `FirstName` → `nombre`
- `LastName1` → `apellido1`
- `LastName2` → `apellido2`

**Nota**: `VATNum` (DNI/NIF) es obligatorio, pero **no** se usa para encontrar al trabajador (puede cambiar).
Se compara contra `trabajadores.nif` **solo cuando hay trabajador activo**; si difiere, se trata como modificación.
Si no hay trabajador activo, la comparación no aplica y se evalúa como alta según fechas.

### Tabla de Referencia: `trabajadores` (base de datos `e03800`)

La tabla `trabajadores` en la base de datos `e03800` contiene los trabajadores actuales/activos.

### Reglas de Negocio

#### CASO 1: Trabajador NO existe en `trabajadores`
- **Condición**: No se encuentra registro en `trabajadores` con los campos `codiemp`, `nombre`, `apellido1`, `apellido2`
- **Acción**: Es un **ALTA** → `tipo = 'A'` en `com_altas`
- **Significado**: Es un nuevo trabajador que no está registrado en el sistema

#### CASO 2: Trabajador SÍ existe en `trabajadores`
- **Condición**: Se encuentra registro(s) en `trabajadores` con los campos coincidentes
- **Importante**: Necesitamos identificar a qué registro pertenece la modificación o alta

- **Primera evaluación: ¿Existe trabajador ACTIVO?**

  **CASO 2.A: SÍ existe trabajador ACTIVO (`fechabaja = NULL` o `fechabaja = ''`)**
  - **Significado**: Hay al menos un registro del trabajador que está activo (no dado de baja)
  - **Validación de NIF (VATNum)**:
    - Si `VATNum` **no coincide** con `trabajadores.nif` del registro activo → **MODIFICACIÓN** (`tipo = 'M'`)
  - **Evaluación del rango**: Verificar que la petición pertenezca al rango de este trabajador activo
    - **Rango**: Desde `fechaalta` del trabajador activo hasta `fechabaja` (si existe) o actualidad
    
    **CASO 2.A.1: La petición SÍ pertenece al rango del trabajador activo**
    - **Condición**: `CreatedDate` está dentro del rango del trabajador activo
    - **Acción**: Es una **MODIFICACIÓN** (tipo pendiente de definir)
    - **Estado**: Caso válido, procesar la solicitud
    
    **CASO 2.A.2: La petición NO pertenece al rango del trabajador activo**
    - **Condición**: `CreatedDate` está fuera del rango del trabajador activo
    - **Significado**: Es una solicitud antigua que no afecta al registro actual
    - **Acción**: **OMITIR** la solicitud (no procesar, no crear registro en `com_altas`)
    - **Razón**: Solo nos centramos en solicitudes que afectan al estado actual

  **CASO 2.B: NO existe trabajador ACTIVO (todos los registros tienen `fechabaja != NULL` y `fechabaja != ''`)**
  - **Significado**: Todos los registros del trabajador están dados de baja
  - **Evaluación de fechas**: Comparar `CreatedDate` con la última `fechabaja` de los registros
    
    **CASO 2.B.1: `CreatedDate` < última `fechabaja` de los registros**
    - **Significado**: La solicitud es anterior a la última fecha de baja
    - **Acción**: Es una **SOLICITUD ANTIGUA** → **OMITIR** (no procesar)
    - **Razón**: No afecta al estado actual, es una petición histórica
    
    **CASO 2.B.2: `CreatedDate` > última `fechabaja` de los registros**
    - **Significado**: La solicitud es posterior a la última fecha de baja
    - **Acción**: Es un **ALTA** → `tipo = 'A'` (nueva petición de alta)
    - **Estado**: Caso válido, procesar la solicitud como alta

#### CASOS PENDIENTES DE DEFINIR
- Más casos de modificación
- Manejo de solicitudes antiguas
- Otros escenarios que se definirán más adelante

### Notas de Implementación

1. **Base de datos `e03800`**: Contiene `trabajadores` y `com_altas`
2. **Base de datos `interbus_365`**: Contiene `dfo_com_altas` (relación ETag ↔ ID)
3. **Consulta a `trabajadores`**: Se debe hacer en la base de datos `e03800` usando los campos de identificación
4. **Campo `tipo` en `com_altas`**: 
   - `'A'` = Alta (cuando trabajador no existe en `trabajadores` o todos están dados de baja con `CreatedDate` > última `fechabaja`)
   - `'M'` = Modificación (cuando trabajador existe activo y la petición pertenece a su rango)

5. **Campo `coditraba` en `com_altas`**:
   - **Si `tipo = 'A'`**: `coditraba = 0` (cero) - nuevo trabajador sin código asignado
   - **Si `tipo = 'M'`**: `coditraba = coditraba` del trabajador activo en `trabajadores` - mantener código existente

6. **Validación de orden cronológico (específica por tipo)**:
   - La validación es **independiente** para ALTAS y MODIFICACIONES
   - **Consulta cruzada entre bases de datos**: Como están en el mismo servidor, se puede hacer JOIN directo usando `interbus_365.dfo_com_altas` y `e03800.com_altas`
   - **Para ALTAS (`tipo = 'A'`)**:
     - El `CreatedDate` debe ser **mayor** al último `created_date` de un registro ALTA del mismo trabajador
     - Consulta con JOIN usando `codiemp`, `nombre`, `apellido1`, `apellido2` y `tipo = 'A'`
   - **Para MODIFICACIONES (`tipo = 'M'`)**:
     - El `CreatedDate` debe ser **mayor** al último `created_date` de un registro MODIFICACIÓN del mismo trabajador
     - Consulta con JOIN usando `codiemp`, `nombre`, `apellido1`, `apellido2`, `tipo = 'M'` y **`coditraba`** (del trabajador activo)
   - Si `CreatedDate` <= último `created_date` del mismo tipo: **OMITIR** el registro (mantener integridad cronológica por tipo)

7. **Manejo de valores NULL y vacíos**:
   - **Valores NULL del endpoint**: Se insertan como `NULL` en `com_altas`
   - **Valores vacíos (string `""`)**: Se insertan como `NULL` en `com_altas`
   - **Campos no mapeados**: Se insertan como `NULL` en `com_altas`

8. **Manejo de conversiones de tipos**:
   - **String a INT** (`HolidaysAbsencesGroupATISAId`, `LibrariesGroupATISAId`, `AdvanceGroupATISAId`):
     - Si el string no es numérico → insertar como `NULL`
     - Si es numérico → convertir a INT
   - **String a DECIMAL** (`Salary`):
     - Si el string no es numérico → insertar como `NULL`
     - Si es numérico → convertir a DECIMAL(14,4)
   - **Datetime ISO a DATE** (`StartDate`, `BirthDate`):
     - Si el formato es inválido → insertar como `NULL`
     - Si es válido → extraer solo la parte de fecha

9. **Orden de creación de registros**:
   - **PRIORITARIO**: Primero crear en `com_altas` (base `e03800`) para obtener el `id` autoincremental
   - Luego crear en `dfo_com_altas` (base `interbus_365`) usando el `id` obtenido
   - Esto permite hacer el JOIN correctamente en futuras validaciones

10. **Conexión a bases de datos**:
    - Se puede usar el mismo conector (`E03800DatabaseAdapter` o similar)
    - Como las bases están en el mismo servidor, se pueden hacer consultas cruzadas directamente en SQL
    - Ejemplo: `SELECT * FROM interbus_365.dfo_com_altas dfo JOIN e03800.com_altas ca ON dfo.id = ca.id`

## Funciones de Base de Datos: Implementación Detallada

### Función: `find_trabajador`

**IMPORTANTE**: Un trabajador puede tener MÚLTIPLES registros en la tabla `trabajadores`. Esta función debe obtener TODOS los registros y evaluar si hay alguno activo.

```python
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
    connection = self._get_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Obtener TODOS los registros del trabajador (no solo uno)
    query = """
        SELECT coditraba, fechaalta, fechabaja, telefono, numeross, nif
        FROM trabajadores
        WHERE codiemp = %s 
          AND nombre = %s 
          AND apellido1 = %s 
          AND apellido2 = %s
        ORDER BY fechaalta DESC
    """
    cursor.execute(query, (codiemp, nombre, apellido1, apellido2))
    all_records = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    if not all_records:
        return None
    
    # Iterar por TODOS los registros para encontrar si hay alguno activo
    active_record = None
    has_active = False
    
    for record in all_records:
        fechabaja = record.get('fechabaja')
        # Verificar si está activo (fechabaja = NULL o vacío)
        if fechabaja is None or fechabaja == '':
            has_active = True
            # Tomar el primer registro activo encontrado (puede haber varios)
            if active_record is None:
                active_record = record
            # No hacer break porque queremos evaluar todos, pero solo guardamos el primero activo
    
    return {
        'exists': True,
        'has_active': has_active,
        'active_record': active_record,  # Puede ser None si todos están dados de baja
        'all_records': all_records  # Lista completa de todos los registros
    }
```

### Función: `get_last_fechabaja`

**IMPORTANTE**: Un trabajador puede tener MÚLTIPLES registros con fechabaja. Necesitamos iterar por TODOS para encontrar la fecha más reciente.

```python
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
    
    cursor.close()
    connection.close()
    
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
```

### Uso de las funciones en el flujo

**En el PASO 2 (Identificación de tipo):**

```python
# Llamar a find_trabajador (retorna dict con información completa)
trabajador_info = e03800_adapter.find_trabajador(codiemp, nombre, apellido1, apellido2)

if trabajador_info is None:
    # CASO 1: No existe ningún registro
    tipo = 'A'
    coditraba = 0
else:
    # CASO 2: Existe (puede tener múltiples registros)
    has_active = trabajador_info.get('has_active', False)
    active_record = trabajador_info.get('active_record')  # Puede ser None
    vatnum = (record.get('VATNum') or '').strip().upper()
    
    if has_active and active_record:
        # CASO 2.A: Hay al menos un registro activo
        fechaalta = active_record.get('fechaalta')
        fechabaja = active_record.get('fechabaja')  # Será NULL o ''
        active_nif = (active_record.get('nif') or '').strip().upper()

        # Si el NIF no coincide con el registro activo, es modificación
        if vatnum and active_nif and vatnum != active_nif:
            tipo = 'M'
            coditraba = active_record.get('coditraba')
        else:
            # Verificar rango
            if self._is_in_range(created_date, fechaalta, fechabaja):
                tipo = 'M'
                coditraba = active_record.get('coditraba')
            else:
                return {'status': 'skipped', 'reason': 'out_of_range'}
    else:
        # CASO 2.B: Todos los registros tienen fechabaja
        ultima_fechabaja = e03800_adapter.get_last_fechabaja(codiemp, nombre, apellido1, apellido2)
        
        if ultima_fechabaja and created_date > ultima_fechabaja:
            tipo = 'A'
            coditraba = 0
        else:
            return {'status': 'skipped', 'reason': 'old_request'}
```

### Notas importantes

1. **`find_trabajador`**:
   - Obtiene TODOS los registros del trabajador (no solo uno)
   - Itera por todos para encontrar si hay alguno activo
   - Retorna el primer registro activo encontrado (si existe)
   - Retorna lista completa de todos los registros

2. **`get_last_fechabaja`**:
   - Obtiene TODOS los registros con fechabaja
   - Itera por todos para encontrar la fecha más reciente
   - No asume que el último registro es el más reciente
   - Compara todas las fechas para encontrar la máxima




datos atisa

empresa ej 03775 atobuses hermanos

  --->categoria  03775
  --->puesto
  --->subpuesto
grupo cotizacion
 situacion cotizacion
 codigo cuentacotizacion
 calendario ->grupo vacaciones
