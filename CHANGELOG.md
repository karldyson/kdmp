# Changelog

All notable changes to kdmp. kdmp isn't versioned separately; consuming projects pin it by submodule commit.

## Unreleased

### Added
- `kdmp.sensors.scd4x`: Sensirion SCD40/41/43 driver. Periodic measurement mode, non-blocking `read()` returning `co2` (int ppm), `temperature` and `humidity`. ID from the 48-bit serial, model from `get_sensor_variant`, optional `temperature_offset`/`altitude` written to RAM at init (never persisted), and self-healing re-init after repeated read failures.
- `SensorDriver.quantities`: class attribute listing the quantities a driver measures (`("temperature", "humidity")` for SHT3x).
- `co2` documented as a reading quantity.

### Changed
- `crc8` and `sleep_ms` moved from `sensors/sht3x.py` to `sensors/base.py` so Sensirion drivers share them. SHT3x behaviour is unchanged.

## Initial release (November 2026)

- `kdmp.log`: levelled logger with lazy `%`-formatting.
- `kdmp.sensors.base`: `SensorDriver` interface (`ids()`, `read()`) and `position_id()`.
- `kdmp.sensors.sht3x`: Sensirion SHT30/31/35 temperature and humidity driver.
