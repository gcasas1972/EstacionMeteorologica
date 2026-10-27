import unittest
from datetime import datetime

from serial_reader import parse_measurement, process_serial_lines


SAMPLE = [
    "Temperatura BMP: 22.46 C",
    "Presion: 1020.04 hPa",
    "Temperatura DHT: 21.20 C",
    "Humedad del aire: 65.00 %",
    "Humedad suelo RAW: 1022",
]


class ParseMeasurementTests(unittest.TestCase):
    def test_parses_sample_and_converts_soil_moisture(self):
        computer_time = datetime(2026, 10, 27, 13, 59, 17)
        measurement = parse_measurement(SAMPLE, measured_at=computer_time)

        self.assertIsNotNone(measurement)
        self.assertEqual(measurement["measured_at"], computer_time)
        self.assertEqual(measurement["temperature_bmp_c"], 22.46)
        self.assertEqual(measurement["pressure_hpa"], 1020.04)
        self.assertEqual(measurement["temperature_dht_c"], 21.2)
        self.assertEqual(measurement["air_humidity_percent"], 65.0)
        self.assertEqual(measurement["soil_raw"], 1022)
        self.assertEqual(measurement["soil_humidity_percent"], 0.14)

    def test_uses_computer_time_when_serial_timestamp_is_absent(self):
        before = datetime.now()

        measurement = parse_measurement(SAMPLE)

        after = datetime.now()
        self.assertGreaterEqual(measurement["measured_at"], before)
        self.assertLessEqual(measurement["measured_at"], after)

    def test_clamps_soil_moisture_endpoints_and_out_of_range_values(self):
        for raw, expected in ((1023, 0.0), (300, 100.0), (1200, 0.0), (100, 100.0)):
            with self.subTest(raw=raw):
                measurement = parse_measurement(
                    [line.replace("1022", str(raw)) for line in SAMPLE]
                )
                self.assertEqual(measurement["soil_humidity_percent"], expected)

    def test_incomplete_measurement_is_ignored(self):
        self.assertIsNone(parse_measurement(SAMPLE[:-1]))

    def test_processes_complete_marked_blocks_once(self):
        saved = []
        lines = ["ruido", "-- NUEVA LECTURA ---", *SAMPLE, "-- NUEVA LECTURA ---", *SAMPLE]

        count = process_serial_lines(lines, saved.append)

        self.assertEqual(count, 2)
        self.assertEqual(len(saved), 2)


if __name__ == "__main__":
    unittest.main()
