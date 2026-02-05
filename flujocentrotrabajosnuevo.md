# Flujo Centro de Trabajos (WorkerPlaces) - Notas de análisis

## Qué se envía actualmente (POST a Dynamics)
- Endpoint: `WorkerPlaces`
- Payload actual (creación):
  - `dataAreaId` = `itb`
  - `EQMWorkerPlaceID` = `codigop + codigodom` (de `contrcen.dbf`)
  - `Description` = concatenación de `VIA`, `CALLE`, `CPOSTAL`, `MUNICIPIO`, `PROVINCIA`
- Update (PATCH): solo `Description` si cambia
- Delete: por `EQMWorkerPlaceID`

## Archivos / funciones implicadas
- `application/bidirectional_sync_use_case.py`
  - `execute()` rama `WorkerPlaces`
  - `_compare_and_sync()` crea/actualiza/elimina
- `infrastructure/e03800_database_adapter.py`
  - `get_worker_places()` (lee DBF `contrcen.dbf`)
- `main.py`
  - `WorkerPlaces` en lista de bidireccionales
- `infrastructure/dynamics_api_adapter.py`
  - `create_entity_data`, `update_entity_data`, `delete_entity_data`

## Origen de datos
- **DBF**: `contrcen.dbf` (sí toca DBF)
  - Campos usados: `CODIGOP`, `CODIGODOM`, `VIA`, `CALLE`, `CPOSTAL`, `MUNICIPIO`, `PROVINCIA`
- **MySQL e03800**: `empresas` (para filtrar `codigop` válidos)
- **Dynamics 365**: entidad `WorkerPlaces`
- **interbus_365**: tabla dinámica `WorkerPlaces` (se guarda tras sync)

## Requerimiento pendiente (nuevo campo)
- Añadir `CompanyIdATISA` al **POST** de `WorkerPlaces`.
  - Debe llevar **solo `codigop`**.
  - No reemplaza `EQMWorkerPlaceID` (que ya incluye `codigop+codigodom`).
  - Necesario exponer `codigop` en `get_worker_places()` o parsearlo desde `EQMWorkerPlaceID`.

## Grupo de cotización / CCC
- **Grupo de cotización**: no se envía en este flujo.
- **CCC** se envía en la entidad `ContributionAccountCodeCCs`:
  - Construido en `get_contribution_account_code_ccs()` (e03800 + contrcen.dbf)
  - POST en `bidirectional_sync_use_case.py` (`EQMCCC`, `EQMWorkerPlaceID`, `VATNum`)
