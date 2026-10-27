import logging
import re
import time
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger(__name__)
START_MARKER = "-- NUEVA LECTURA ---"
NUMBER = r"([-+]?\d+(?:[.,]\d+)?)"


def _number(pattern: str, text: str) -> Optional[float]:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def parse_measurement(lines, measured_at: Optional[datetime] = None):
    """Convierte una lectura completa del formato serial a campos de base de datos."""
    text = "\n".join(lines)
    temperature_bmp = _number(r"Temperatura BMP:\s*" + NUMBER, text)
    pressure = _number(r"Presion:\s*" + NUMBER, text)
    temperature_dht = _number(r"Temperatura DHT:\s*" + NUMBER, text)
    air_humidity = _number(r"Humedad del aire:\s*" + NUMBER, text)
    soil_match = re.search(r"Humedad suelo RAW:\s*(\d+)", text, re.IGNORECASE)
    if (
        temperature_bmp is None
        or pressure is None
        or temperature_dht is None
        or air_humidity is None
        or soil_match is None
    ):
        return None

    soil_raw = int(soil_match.group(1))
    soil_humidity = min(100.0, max(0.0, (1023 - soil_raw) * 100.0 / (1023 - 300)))
    return {
        "measured_at": measured_at if measured_at is not None else datetime.now(),
        "temperature_bmp_c": temperature_bmp,
        "pressure_hpa": pressure,
        "temperature_dht_c": temperature_dht,
        "air_humidity_percent": air_humidity,
        "soil_raw": soil_raw,
        "soil_humidity_percent": round(soil_humidity, 2),
    }


def process_serial_lines(lines, save: Callable):
    """Procesa líneas seriales y guarda cada bloque completo una sola vez."""
    in_measurement = False
    current_lines = []
    saved = 0
    for raw_line in lines:
        line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else raw_line
        line = line.strip()
        if START_MARKER in line:
            in_measurement = True
            current_lines = []
            continue
        if not in_measurement:
            continue
        current_lines.append(line)
        measurement = parse_measurement(current_lines)
        if measurement is not None:
            save(measurement)
            saved += 1
            in_measurement = False
            current_lines = []
    return saved


def run_serial_reader(port: str, baud_rate: int, save: Callable):
    import serial

    while True:
        try:
            logger.info("Conectando al puerto serial %s a %s baudios", port, baud_rate)
            with serial.Serial(port, baud_rate, timeout=1) as connection:
                logger.info("Puerto serial conectado: %s", port)
                current_lines = []
                in_measurement = False
                while True:
                    line = connection.readline().decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    if START_MARKER in line:
                        in_measurement = True
                        current_lines = []
                        continue
                    if not in_measurement:
                        continue
                    current_lines.append(line)
                    measurement = parse_measurement(current_lines)
                    if measurement is not None:
                        try:
                            save(measurement)
                            logger.info("Medición guardada: %s", measurement["measured_at"])
                        except Exception:
                            logger.exception("No se pudo guardar la medición recibida")
                        in_measurement = False
                        current_lines = []
        except (serial.SerialException, OSError):
            logger.exception("No se pudo leer el puerto serial %s; reintentando en 5 segundos", port)
            time.sleep(5)
