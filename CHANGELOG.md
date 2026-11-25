# Changelog

All notable changes to kdmp.

Releases are tagged `vX.Y.Z`. Below 1.0.0, a minor version can change the API. Consuming projects pin kdmp by submodule commit, which should be a tagged release.

## [0.2.0] - 2026-11-25

### Added
- `kdmp.sensors.scd4x`: Sensirion SCD40/41/43 driver. Periodic measurement mode, non-blocking `read()` returning `co2` (int ppm), `temperature` and `humidity`. ID from the 48-bit serial, model from `get_sensor_variant`, optional `temperature_offset`/`altitude` written to RAM at init (never persisted), and self-healing re-init after repeated read failures.
- `SensorDriver.quantities`: class attribute listing the quantities a driver measures (`("temperature", "humidity")` for SHT3x).
- `co2` documented as a reading quantity.

### Changed
- `crc8` and `sleep_ms` moved from `sensors/sht3x.py` to `sensors/base.py` so Sensirion drivers share them. SHT3x behaviour is unchanged.

## [0.1.0] - 2026-11-20

Initial release.

- `kdmp.log`: levelled logger with lazy `%`-formatting.
- `kdmp.sensors.base`: `SensorDriver` interface (`ids()`, `read()`) and `position_id()`.
- `kdmp.sensors.sht3x`: Sensirion SHT30/31/35 temperature and humidity driver.

[0.2.0]: https://github.com/karldyson/kdmp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/karldyson/kdmp/releases/tag/v0.1.0
