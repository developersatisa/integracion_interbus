# Guía de Uso - Integración Interbus 365

## Inicio Rápido

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Credenciales


### 3. Crear Base de Datos

**Opción 1: Usando el script SQL**

```bash
mysql -u root -p < database/create_database.sql
```

**Opción 2: Usando Python**

```bash
python scripts/initialize_db.py
```

**Opción 3: Manualmente**

```sql
CREATE DATABASE IF NOT EXISTS interbus_365 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE interbus_365;
-- Continúa con el resto del script de database/create_database.sql
```

### 4. Ejecutar la Sincronización

**Sincronizar todas las entidades:**

```bash
python3 main.py
```

**Sincronizar una entidad específica:**

```bash
python3 main.py CompanyATISAs
```

## Ejemplos de Uso

### Verificar Token de Autenticación

```python
from infrastructure.token_service import AzureADTokenService

token_service = AzureADTokenService()
token = token_service.get_access_token()
print(f"Token: {token[:50]}...")
```

### Sincronizar una Entidad Manualmente

```python
from infrastructure.token_service import AzureADTokenService
from infrastructure.dynamics_api_adapter import DynamicsAPIAdapter
from infrastructure.database_adapter import MySQLDatabaseAdapter
from application.use_cases import SyncDynamicsEntityUseCase

# Setup
token_service = AzureADTokenService()
dynamics_api = DynamicsAPIAdapter()
database_adapter = MySQLDatabaseAdapter()

# Inicializar base de datos
database_adapter.initialize_database()

# Crear caso de uso
use_case = SyncDynamicsEntityUseCase(token_service, dynamics_api, database_adapter)

# Ejecutar sincronización
result = use_case.execute('CompanyATISAs')
print(result)
```

### Consultar Datos Guardados

```python
import mysql.connector
from config.settings import settings

# Conectar a la base de datos
conn = mysql.connector.connect(
    host=settings.db_host,
    user=settings.db_user,
    password=settings.db_password,
    database=settings.db_name
)

cursor = conn.cursor()

# Consultar registros de una entidad
cursor.execute("SELECT * FROM dynamic_entities WHERE entity_name = 'CompanyATISAs'")
records = cursor.fetchall()

for record in records:
    print(record)

cursor.close()
conn.close()
```

## Entidades Disponibles

- `CompanyATISAs` - Compañías ATISAs
- `WorkerPlaces` - Lugares de Trabajo
- `ContributionAccountCodeCCs` - Códigos de Cuenta de Contribución
- `HolidaysAbsencesGroupATISAs` - Grupos de Vacaciones y Ausencias
- `VacationBalances` - Balances de Vacaciones
- `IncidentGroupATISAs` - Grupos de Incidentes
- `AdvanceGroupATISAs` - Grupos de Avances
- `LibrariesGroupATISAs` - Grupos de Bibliotecas
- `LeaveGroupATISAs` - Grupos de Licencias
- `VacationCalenders` - Calendarios de Vacaciones
- `HighsLowsChanges` - Cambios de Altas y Bajas

## Estructura de la Base de Datos

### Tabla: dynamic_entities

Almacena todos los datos de las entidades en formato JSON:

```sql
CREATE TABLE dynamic_entities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_name VARCHAR(100) NOT NULL,
    json_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Consultar Datos

```sql
-- Ver todos los registros de una entidad
SELECT * FROM dynamic_entities WHERE entity_name = 'CompanyATISAs';

-- Contar registros por entidad
SELECT entity_name, COUNT(*) as count 
FROM dynamic_entities 
GROUP BY entity_name;

-- Ver datos JSON de un registro específico
SELECT json_data FROM dynamic_entities 
WHERE id = 1;
```

## Flujo de Trabajo

1. **Autenticación**: Obtiene token de Azure AD
2. **Obtención de Datos**: Consulta cada entidad de Dynamics 365
3. **Limpieza**: Borra datos antiguos de la base de datos
4. **Almacenamiento**: Guarda los nuevos datos en JSON

## Troubleshooting

### Error: No existe la base de datos

```bash
# Crear base de datos manualmente
mysql -u root -p -e "CREATE DATABASE interbus_365 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### Error: Credenciales incorrectas

Verifica el archivo `.env` y asegúrate de que las credenciales sean correctas.

### Error: Token expirado

Los tokens se generan automáticamente en cada ejecución. Si el error persiste, verifica las credenciales de Azure AD.

### Error: Entidad no encontrada

Verifica que el nombre de la entidad sea correcto y que exista en Dynamics 365.

## Programación Automática (Windows Task Scheduler)

### Crear tarea programada

1. Abre Task Scheduler
2. Crear Tarea Básica
3. Nombre: "Sincronización Interbus 365"
4. Trigger: Diario a las 6:00 AM
5. Acción: Iniciar programa
   - Programa: `C:\Python\python.exe`
   - Argumentos: `X:\ruta\al\proyecto\main.py`
   - Iniciar en: `X:\ruta\al\proyecto`

## Logs

Los logs se muestran en la consola por defecto. Para guardar en archivo:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sincronizacion.log'),
        logging.StreamHandler()
    ]
)
```

## Soporte

Para más información, consulta:
- `README.md` - Documentación general
- `database/create_database.sql` - Script de creación de BD
- `examples/sync_example.py` - Ejemplos de uso


