# 🚀 Inicio Rápido - Integración Interbus 365

## ⚡ 3 Pasos para Empezar

### 1️⃣ Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2️⃣ Configurar Base de Datos

```bash
# Ejecutar script SQL
mysql -u root -p < database/create_database.sql
```

O crear el archivo `.env` desde `env.example`:

```bash
copy env.example .env
# Editar .env con tus credenciales MySQL
```

### 3️⃣ Ejecutar

```bash
# Sincronizar todas las entidades
python main.py

# O sincronizar una entidad específica
python main.py CompanyATISAs
```

## 📋 Configuración Mínima Requerida





## ✅ Verificar que Funciona

```bash
python main.py CompanyATISAs
```

Deberías ver:
```
✓ CompanyATISAs: X registros sincronizados
```

## 📚 Documentación Completa

- `INSTALL.md` - Guía de instalación detallada
- `USAGE.md` - Guía de uso y ejemplos
- `README.md` - Documentación completa
- `ESTRUCTURA_PROYECTO.md` - Arquitectura del proyecto

## 🆘 Problemas Comunes

### Error: No module named 'pydantic_settings'
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Error: Can't connect to MySQL
```bash
# Verificar que MySQL está corriendo
net start MySQL80  # Windows
```

### Error: No existe base de datos
```bash
mysql -u root -p -e "CREATE DATABASE interbus_365 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

## 🎯 Próximos Pasos

1. Lee `USAGE.md` para ejemplos avanzados
2. Revisa `ESTRUCTURA_PROYECTO.md` para entender la arquitectura
3. Consulta `examples/sync_example.py` para ver código de ejemplo

¡Listo para usar! 🎉


