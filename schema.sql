CREATE DATABASE IF NOT EXISTS estacion_meteorologica
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE estacion_meteorologica;

CREATE TABLE IF NOT EXISTS measurements (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  measured_at DATETIME NOT NULL,
  temperature_bmp_c DECIMAL(6, 2) NOT NULL,
  pressure_hpa DECIMAL(8, 2) NOT NULL,
  temperature_dht_c DECIMAL(6, 2) NOT NULL,
  air_humidity_percent DECIMAL(5, 2) NOT NULL,
  soil_raw SMALLINT UNSIGNED NOT NULL,
  soil_humidity_percent DECIMAL(5, 2) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_measurements_measured_at (measured_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
