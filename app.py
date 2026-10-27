import logging
import os
import threading
import mysql.connector
from flask import Flask, jsonify, render_template, request
from mysql.connector import Error

from serial_reader import run_serial_reader

app = Flask(__name__)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
)

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "estacion_meteorologica"),
}
MAX_MEASUREMENTS = 500
_database_ready = False
_database_lock = threading.Lock()


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def ensure_database_table():
    global _database_ready
    with _database_lock:
        if _database_ready:
            return
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            connection.commit()
            _database_ready = True
        finally:
            connection.close()


def save_measurement(measurement):
    ensure_database_table()
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO measurements (
                measured_at, temperature_bmp_c, pressure_hpa,
                temperature_dht_c, air_humidity_percent,
                soil_raw, soil_humidity_percent
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                measurement["measured_at"],
                measurement["temperature_bmp_c"],
                measurement["pressure_hpa"],
                measurement["temperature_dht_c"],
                measurement["air_humidity_percent"],
                measurement["soil_raw"],
                measurement["soil_humidity_percent"],
            ),
        )
        connection.commit()
    finally:
        connection.close()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/measurements")
def measurements():
    try:
        ensure_database_table()
        limit = min(max(request.args.get("limit", 200, type=int), 1), MAX_MEASUREMENTS)
        connection = get_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, measured_at, temperature_bmp_c, pressure_hpa,
                       temperature_dht_c, air_humidity_percent, soil_raw,
                       soil_humidity_percent
                FROM measurements
                ORDER BY measured_at DESC, id DESC
                LIMIT %s
                """,
                (limit,),
            )
            records = cursor.fetchall()
        finally:
            connection.close()

        for record in records:
            record["measured_at"] = record["measured_at"].isoformat(sep=" ")
            for key, value in record.items():
                if key != "measured_at" and key != "id":
                    record[key] = float(value)
        return jsonify(list(reversed(records)))
    except Error:
        app.logger.exception("No se pudieron consultar las mediciones")
        return jsonify({"error": "No se pudieron consultar las mediciones. Revise la conexión con MySQL."}), 503


def start_serial_reader():
    serial_port = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")
    baud_rate = int(os.getenv("SERIAL_BAUD_RATE", "9600"))
    thread = threading.Thread(
        target=run_serial_reader,
        args=(serial_port, baud_rate, save_measurement),
        name="serial-reader",
        daemon=True,
    )
    thread.start()


if __name__ == "__main__":
    start_serial_reader()
    app.run(
        host=os.getenv("WEB_HOST", "127.0.0.1"),
        port=int(os.getenv("WEB_PORT", "5000")),
        debug=False,
        use_reloader=False,
    )
