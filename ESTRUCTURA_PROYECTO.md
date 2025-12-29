# Estructura del Proyecto - Arquitectura Hexagonal

```
integracion_interbus/
│
├── 📁 application/              # Capa de aplicación (casos de uso)
│   ├── __init__.py
│   └── use_cases.py             # Casos de uso que orquestan la lógica
│
├── 📁 config/                   # Configuración
│   ├── __init__.py
│   ├── settings.py              # Configuración con pydantic-settings
│   └── logging_config.py       # Configuración de logging
│
├── 📁 database/                 # Scripts de base de datos
│   ├── __init__.py
│   └── create_database.sql     # Script de creación de base de datos
│
├── 📁 domain/                   # Capa de dominio (hexagonal)
│   ├── __init__.py
│   ├── entities.py             # Entidades del dominio
│   ├── ports.py                # Puertos (interfaces) - DIP
│   └── constants.py            # Constantes y configuraciones
│
├── 📁 infrastructure/           # Capa de infraestructura (adaptadores)
│   ├── __init__.py
│   ├── token_service.py        # Adaptador para Azure AD
│   ├── dynamics_api_adapter.py # Adaptador para API Dynamics 365
│   └── database_adapter.py     # Adaptador para MySQL
│
├── 📁 examples/                 # Ejemplos de uso
│   ├── __init__.py
│   └── sync_example.py         # Ejemplos de código
│
├── 📁 scripts/                  # Scripts de utilidad
│   ├── __init__.py
│   └── initialize_db.py        # Script para inicializar BD
│
├── 📁 utils/                    # Utilidades
│   ├── __init__.py
│   └── validators.py           # Validadores de configuración
│
├── 📄 main.py                   # Punto de entrada principal
├── 📄 requirements.txt          # Dependencias de Python
├── 📄 env.example               # Ejemplo de configuración
├── 📄 README.md                 # Documentación principal
├── 📄 USAGE.md                  # Guía de uso detallada
├── 📄 INSTALL.md                # Guía de instalación
└── 📄 ESTRUCTURA_PROYECTO.md    # Este archivo
```

## Arquitectura Hexagonal

### Capa de Dominio (`domain/`)
Contiene la lógica de negocio pura, sin dependencias externas:
- **Entidades**: Representan las entidades de Dynamics 365
- **Puertos**: Interfaces que definen los contratos (DIP)
- **Constantes**: Configuraciones del dominio

### Capa de Aplicación (`application/`)
Orquesta los casos de uso:
- **Casos de uso**: Lógica de aplicación que combina puertos
- Sigue el principio SRP (Single Responsibility)

### Capa de Infraestructura (`infrastructure/`)
Implementa los adaptadores concretos:
- **Token Service**: Autenticación con Azure AD
- **Dynamics API Adapter**: Interacción con Dynamics 365
- **Database Adapter**: Interacción con MySQL

### Capa de Configuración (`config/`)
Gestión de configuración y logging:
- **Settings**: Variables de entorno con pydantic-settings
- **Logging**: Configuración de logging

## Principios SOLID Aplicados

### 1. Single Responsibility Principle (SRP)
- Cada clase tiene una única responsabilidad
- `TokenService` solo maneja tokens
- `DynamicsAPIAdapter` solo maneja llamadas a la API
- `DatabaseAdapter` solo maneja la BD

### 2. Open/Closed Principle (OCP)
- Abierto a extensión, cerrado a modificación
- Se pueden agregar nuevos adaptadores sin modificar código existente
- Nuevas entidades se agregan a `ENTITIES` en constants.py

### 3. Liskov Substitution Principle (LSP)
- Los adaptadores pueden sustituirse entre sí
- Cualquier implementación de un puerto puede usarse

### 4. Interface Segregation Principle (ISP)
- Interfaces pequeñas y específicas
- `TokenRepository`, `DynamicsAPIAdapter`, `DatabaseAdapter` son específicas

### 5. Dependency Inversion Principle (DIP)
- Depende de abstracciones (puertos), no de implementaciones
- Los casos de uso dependen de las interfaces en `ports.py`

## Flujo de Datos

```
main.py
    ↓
application/use_cases.py (Casos de uso)
    ↓
domain/ports.py (Interfaces/Contratos)
    ↓
infrastructure/*.py (Implementaciones)
    ↓
API MySQL
```

## Componentes Principales

### 1. Authentication Flow
```
Azure AD → Token → Dynamics 365 API
```

### 2. Sync Flow
```
Token Service → Get Token
    ↓
Dynamics API → Get Entity Data
    ↓
Database → Save Entity Data
    ↓
Log Results
```

### 3. Entities Supported
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

## Ventajas de esta Arquitectura

1. **Testeable**: Cada capa se puede testear independientemente
2. **Mantenible**: Cambios en infraestructura no afectan el dominio
3. **Escalable**: Fácil agregar nuevos adaptadores o entidades
4. **Reutilizable**: Los casos de uso pueden reutilizarse
5. **Desacoplado**: Las capas no conocen las implementaciones

## Extensiones Futuras

Para agregar nuevas funcionalidades:

1. **Nueva entidad**: Agregar a `ENTITIES` en `domain/constants.py`
2. **Nueva fuente de datos**: Implementar adaptador en `infrastructure/`
3. **Nuevo caso de uso**: Agregar en `application/use_cases.py`
4. **Nueva validación**: Agregar en `utils/validators.py`


