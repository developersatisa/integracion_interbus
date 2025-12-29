# Integración Interbus 365

Proyecto de Python para sincronizar entidades de Dynamics 365 con una base de datos MySQL.

Documentacion , en esta WEB tenemos disponible ejemplos de conexion con todos los metodos. - https://axparadise.com/how-to-use-postman-to-access-d365fo-odata-endpoint/

## Arquitectura

Este proyecto sigue los principios de **arquitectura hexagonal** y **SOLID**:

- **Domain**: Entidades y puertos (interfaces)
- **Application**: Casos de uso
- **Infrastructure**: Adaptadores (implementaciones concretas)
- **Config**: Configuración

## Requisitos

- Python 3.8+
- MySQL 8.0+
- Credenciales de Azure AD

## Instalación

1. Clonar el repositorio

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar .env con tus credenciales
```

## Configuración

Editar el archivo `.env` con tus credenciales:

```env
# Azure AD Credentials
AZURE_AD_CLIENT_ID=tu_client_id
AZURE_AD_CLIENT_SECRET=tu_client_secret
AZURE_AD_TENANT_ID=tu_tenant_id
AZURE_AD_RESOURCE=https://interbus-test.sandbox.operations.eu.dynamics.com

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_password
DB_NAME=interbus_365

# API Configuration
API_BASE_URL=interbus-test.sandbox.operations.eu.dynamics.com
```

## Crear Base de Datos

Ejecutar el script SQL para crear la base de datos y tablas:

```bash
mysql -u root -p < database/create_database.sql
```

O ejecutar manualmente en MySQL:

```sql
CREATE DATABASE IF NOT EXISTS interbus_365;
USE interbus_365;
-- ... (ver archivo database/create_database.sql)
```

## Uso

### Sincronizar todas las entidades:

```bash
python main.py
```

### Sincronizar una entidad específica:

```bash
python main.py CompanyATISAs
```

### Verificar la Instalación:

Antes de ejecutar, verifica que todo esté configurado correctamente:

```bash
python scripts/check_environment.py
```

Este script verifica:
- ✓ Versión de Python
- ✓ Dependencias instaladas
- ✓ Configuración válida
- ✓ Conexión a MySQL
- ✓ Credenciales de Azure AD

## Entidades Soportadas

- CompanyATISAs
- WorkerPlaces
- ContributionAccountCodeCCs
- HolidaysAbsencesGroupATISAs
- VacationBalances
- IncidentGroupATISAs
- AdvanceGroupATISAs
- LibrariesGroupATISAs
- LeaveGroupATISAs
- VacationCalenders
- HighsLowsChanges

## Estructura del Proyecto

```
├── application/          # Capa de aplicación (casos de uso)
├── config/              # Configuración
├── database/            # Scripts SQL
├── domain/              # Capa de dominio (entidades y puertos)
├── infrastructure/      # Capa de infraestructura (adaptadores)
├── main.py             # Punto de entrada
├── requirements.txt     # Dependencias
└── README.md           # Documentación
```

## Principios SOLID Aplicados

1. **S**ingle Responsibility Principle (SRP): Cada clase tiene una única responsabilidad
2. **O**pen/Closed Principle (OCP): Abierto a extensión, cerrado a modificación
3. **L**iskov Substitution Principle (LSP): Las implementaciones pueden sustituirse
4. **I**nterface Segregation Principle (ISP): Interfaces pequeñas y específicas
5. **D**ependency Inversion Principle (DIP): Dependencias de abstracciones, no de concretas

## Arquitectura Hexagonal

- **Puertos**: Interfaces en `domain/ports.py`
- **Adaptadores**: Implementaciones en `infrastructure/`
- **Casos de uso**: Lógica de aplicación en `application/use_cases.py`

## Autenticación

El sistema utiliza el flujo **client credentials** de Azure AD para obtener tokens de acceso:

1. Obtiene token de Azure AD
2. Usa el token para autenticarse con Dynamics 365
3. Obtiene datos de las entidades
4. Guarda los datos en MySQL

## Base de Datos

La base de datos utiliza una tabla genérica `dynamic_entities` que almacena:

- `id`: Identificador único
- `entity_name`: Nombre de la entidad
- `json_data`: Datos JSON de la entidad
- `created_at`: Fecha de creación
- `updated_at`: Fecha de actualización

## Logging

El sistema genera logs detallados de todas las operaciones, incluyendo:

- Inicio de sincronización
- Resultados por entidad
- Errores y excepciones

## Troubleshooting

### Error de conexión a MySQL
Verificar credenciales en `.env` y que MySQL esté ejecutándose.

### Error de autenticación con Azure AD
Verificar las credenciales en `.env` y que las entidades existan en Dynamics 365.

### Error al obtener datos de una entidad
Verificar que el nombre de la entidad sea correcto y que exista en Dynamics 365.

## Licencia

Proyecto propietario - Integración Interbus 365

