# Guía de Instalación Rápida

## Requisitos Previos

- Python 3.8 o superior
- MySQL 8.0 o superior
- Git (opcional)

## Paso 1: Clonar o Descargar el Proyecto

```bash
# Si usas Git
git clone <url-del-repositorio>
cd integracion_interbus

# O simplemente descomprimir el archivo ZIP
```

## Paso 2: Instalar Dependencias de Python

```bash
pip install -r requirements.txt
```

## Paso 3: Configurar Credenciales

### Opción A: Usar el archivo .env (Recomendado)

1. Copia el archivo de ejemplo:
```bash
copy env.example .env
# En Linux/Mac: cp env.example .env
```

2. Edita el archivo `.env` con tus credenciales:

### Opción B: Modificar config/settings.py directamente

No recomendado, pero puedes editar el archivo directamente.

## Paso 4: Crear la Base de Datos

### Opción 1: Usando el Script SQL (Más Simple)

```bash
mysql -u root -p < database/create_database.sql
```

Te pedirá la contraseña de MySQL. Esto creará:
- La base de datos `interbus_365`
- Las tablas necesarias

### Opción 2: Usando Python

```bash
python scripts/initialize_db.py
```

### Opción 3: Manualmente

Conéctate a MySQL y ejecuta:

```sql
CREATE DATABASE IF NOT EXISTS interbus_365 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE interbus_365;
-- Y luego ejecuta el contenido de database/create_database.sql
```

## Paso 5: Verificar la Instalación

Ejecuta un test para verificar que todo esté configurado correctamente:

```bash
python main.py CompanyATISAs
```

Esto sincronizará solo una entidad para verificar que:
- Las credenciales de Azure AD funcionan
- La conexión a MySQL funciona
- La API responde correctamente

## Paso 6: Ejecutar la Sincronización Completa

```bash
python main.py
```

Esto sincronizará todas las 11 entidades disponibles.

## Resumen de Archivos Importantes

- `.env` - Configuración de credenciales (crear a partir de env.example)
- `database/create_database.sql` - Script de creación de BD
- `main.py` - Punto de entrada de la aplicación
- `README.md` - Documentación general
- `USAGE.md` - Guía de uso detallada

## Solución de Problemas

### Error: No module named 'pydantic_settings'

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Error: Can't connect to MySQL

Verifica que MySQL esté ejecutándose:
```bash
# Windows
net start MySQL80

# Linux/Mac
sudo systemctl start mysql
```

### Error: Authentication failed

Verifica las credenciales en el archivo `.env`:
- Las credenciales de Azure AD deben ser correctas
- La contraseña de MySQL debe ser la correcta

### Error: No existe la base de datos

```bash
mysql -u root -p -e "CREATE DATABASE interbus_365 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

## Siguiente Paso

Una vez instalado, consulta `USAGE.md` para ejemplos de uso avanzado.


