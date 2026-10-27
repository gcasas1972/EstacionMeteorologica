# Estación meteorológica

Aplicación local que recibe lecturas por puerto serial, las guarda en MySQL y
presenta una tabla y gráficos en una página web.

## Requisitos

- Python 3.10 o posterior.
- MySQL Server local.
- Puerto serial del microcontrolador y velocidad configurados iguales en ambos
  extremos (por defecto, `/dev/ttyUSB0` a 9600 baudios).

## Instalación y ejecución

1. Cree la base de datos y la tabla:

   ```sh
   mysql -u root -p < schema.sql
   ```

2. Cree y active un entorno virtual e instale las dependencias:

   ```sh
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure las variables de entorno de `.env.example` en su terminal. Ajuste
   al menos `MYSQL_USER`, `MYSQL_PASSWORD` y `SERIAL_PORT` según su instalación.
   El programa no carga archivos `.env` automáticamente.

4. Inicie la aplicación:

   ```sh
   python app.py
   ```

5. Abra <http://127.0.0.1:5000>.

La aplicación crea la tabla `measurements` si aún no existe. El usuario MySQL
configurado necesita permisos para crear tablas y leer/escribir datos en la
base seleccionada.

## Formato serial

Cada lectura debe comenzar con `-- NUEVA LECTURA ---` y contener los siguientes
campos. La fecha y hora que pueda enviar el dispositivo se ignora: la aplicación
registra la fecha y hora local de la computadora cuando recibe la lectura.

```text
Temperatura BMP: 22.46 C
Presion: 1020.04 hPa
Temperatura DHT: 21.20 C
Humedad del aire: 65.00 %
Humedad suelo RAW: 1022
```

La humedad del suelo se calcula linealmente entre RAW 1023 (0 %) y RAW 300
(100 %); lecturas fuera de ese rango se limitan a 0–100 %. El panel se actualiza
cada cinco segundos y muestra hasta las 200 lecturas más recientes. La API
`/api/measurements?limit=200` permite consultar hasta 500.
