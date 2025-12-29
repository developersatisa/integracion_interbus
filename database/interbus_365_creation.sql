-- =====================================================
-- SCRIPT DE CREACIÓN DE BASE DE DATOS INTERBUS 365
-- =====================================================
-- Ejecutar este script para crear toda la estructura
-- de la base de datos necesaria para la integración.
-- =====================================================

-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS interbus_365 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE interbus_365;

-- =====================================================
-- TABLA: dynamic_entities
-- Almacena todos los datos de las entidades de Dynamics 365
-- en formato JSON para máxima flexibilidad
-- =====================================================
CREATE TABLE IF NOT EXISTS dynamic_entities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_name VARCHAR(100) NOT NULL COMMENT 'Nombre de la entidad de Dynamics 365',
    json_data TEXT NOT NULL COMMENT 'Datos JSON de la entidad',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Fecha de actualización',
    INDEX idx_entity_name (entity_name),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tabla genérica para almacenar entidades de Dynamics 365';

-- =====================================================
-- TABLA: sync_logs
-- Registra todas las sincronizaciones realizadas
-- =====================================================
CREATE TABLE IF NOT EXISTS sync_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_name VARCHAR(100) NOT NULL COMMENT 'Nombre de la entidad sincronizada',
    records_synced INT NOT NULL COMMENT 'Número de registros sincronizados',
    status VARCHAR(20) NOT NULL COMMENT 'Estado: success, failed',
    error_message TEXT COMMENT 'Mensaje de error si falló',
    sync_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de sincronización',
    INDEX idx_entity_name (entity_name),
    INDEX idx_status (status),
    INDEX idx_sync_date (sync_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Log de sincronizaciones';

-- =====================================================
-- TABLA: token_cache
-- Cache de tokens para optimizar llamadas (opcional)
-- =====================================================
CREATE TABLE IF NOT EXISTS token_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token TEXT NOT NULL COMMENT 'Token de acceso',
    expires_at TIMESTAMP NOT NULL COMMENT 'Fecha de expiración',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación',
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Cache de tokens de autenticación';

-- =====================================================
-- INSERTS DE CONFIGURACIÓN (opcional)
-- =====================================================

-- Mensaje de confirmación
SELECT 'Base de datos interbus_365 creada correctamente' AS mensaje;


