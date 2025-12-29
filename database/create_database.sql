-- Script de creación de base de datos y tablas para Interbus 365
-- Ejecutar este script para crear la estructura de la base de datos

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS interbus_365 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE interbus_365;

-- Tabla genérica para almacenar todas las entidades de Dynamics 365
CREATE TABLE IF NOT EXISTS dynamic_entities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_name VARCHAR(100) NOT NULL,
    json_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_entity_name (entity_name),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de auditoría para registrar las sincronizaciones
CREATE TABLE IF NOT EXISTS sync_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_name VARCHAR(100) NOT NULL,
    records_synced INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    sync_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity_name (entity_name),
    INDEX idx_sync_date (sync_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla para tokens (opcional, para cache)
CREATE TABLE IF NOT EXISTS token_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de relación entre com_altas y EmployeeModifications (ETags)
-- Esta tabla almacena la relación entre los registros de com_altas (e03800)
-- y los ETags de Dynamics 365 para evitar duplicados y rastrear sincronizaciones
CREATE TABLE IF NOT EXISTS dfo_com_altas (
    id INT(10) UNSIGNED NOT NULL PRIMARY KEY COMMENT 'ID de com_altas (referencia directa, sin codificar)',
    etag VARCHAR(255) NOT NULL COMMENT 'Valor de @odata.etag del endpoint codificado en base64 (tiene caracteres especiales)',
    personnel_number VARCHAR(50) DEFAULT NULL COMMENT 'PersonnelNumber del endpoint (para referencia rápida)',
    created_date DATETIME NOT NULL COMMENT 'CreatedDate del endpoint EmployeeModifications (para validación de orden cronológico)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación del registro en esta tabla',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Fecha de actualización del registro',
    INDEX idx_etag (etag),
    INDEX idx_personnel_number (personnel_number),
    INDEX idx_created_date (created_date) COMMENT 'Índice para validación de orden cronológico',
    UNIQUE KEY uk_etag (etag) COMMENT 'Garantiza que cada ETag solo se procese una vez',
    FOREIGN KEY (id) REFERENCES e03800.com_altas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


