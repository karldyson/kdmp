# kdmp

Reusable MicroPython helpers that don't depend on a particular board. They are meant to run on the Raspberry Pi Pico / Pico 2 W, ESP32 and similar boards. This repo is designed to be included in projects as a git submodule mounted at `kdmp/`, so the code imports as `kdmp.<module>`.

## Contents

| Module | Purpose |
|---|---|
| `kdmp.log` | Levelled logger (`debug`/`info`/`warning`/`error`/`off`) with lazy formatting |
| `kdmp.sensors.base` | The driver interface that every sensor implements, plus shared helpers |
| `kdmp.sensors.sht3x` | Sensirion SHT30/31/35 temperature and humidity sensors over I2C |
| `kdmp.sensors.scd4x` | Sensirion SCD40/41/43 CO2 sensors (with their own temperature and humidity) over I2C |

Networking (Wi-Fi, UDP) is planned.

## Rules

- **No board assumptions.** Drivers take `machine.I2C` / `machine.Pin` objects from the caller and never create pins or buses themselves.
- Log through `kdmp.log`, never through `print` directly. Drivers also accept a `log=` override.
- A file is named after a sensor only if it handles that sensor alone. Generic code gets a generic name.

## Logging

```python
from kdmp import log
log.set_level("debug")      # "info" (default), "warning", "error", "off"
_log = log.get("main")
_log.debug("raw=%s", raw)   # formatted only if debug is enabled
```

Use `"debug"` when a console is attached. Use `"warning"` or `"off"` in production. With no USB host attached, output is discarded, but formatting it still costs CPU time and allocations.

## Sensor interface

```python
drv.ids()   # ["20e80802"]  physical IDs found at init
drv.read()  # [{"sensor": "20e80802", "model": "sht30", "temperature": 20.92, "humidity": 49.9}]
```

- Quantities: `temperature` (°C, float), `humidity` (%RH, float), `co2` (ppm, int).
- `drv.quantities` is a tuple of the quantities the driver measures, e.g. `("temperature", "humidity")`. It's a class attribute, so callers can see what a sensor provides before reading it.
- `read()` returns one reading per physical sensor. A single driver can cover several sensors, for example a 1-Wire bus.
- Quantities a sensor doesn't measure are left out of its reading. They are never `None`.
- A sensor that fails to read is left out of the list.
- `read()` never raises an exception.

### SHT3x

```python
from machine import I2C, Pin
from kdmp.sensors.sht3x import SHT3x
sht = SHT3x(I2C(1, sda=Pin(26), scl=Pin(27), freq=100000), addr=0x44, bus=1)
```

- **ID:** the sensor's 32-bit serial number (command `0x3682`, CRC-checked), formatted as 8 hex digits. If the serial can't be read, the ID falls back to `<board unique_id>-i2c<bus>-<addr>`. That fallback identifies the position on the board, not the probe itself.
- **Reading:** single-shot, high repeatability. The driver retries once on an I/O error or CRC failure, then skips that reading.

### SCD4x

```python
from machine import I2C, Pin
from kdmp.sensors.scd4x import SCD4x
scd = SCD4x(I2C(0, sda=Pin(4), scl=Pin(5), freq=100000), addr=0x62, bus=0)
scd.read()  # [{"sensor": "1cab65073b57", "model": "scd41", "co2": 465, "temperature": 23.15, "humidity": 38.8}]
```

- **ID:** the sensor's 48-bit serial number (command `0x3682`, CRC-checked), formatted as 12 hex digits. Falls back to the position ID, as for SHT3x.
- **Model:** the `model=` argument if given, otherwise read from the sensor (`get_sensor_variant`: `scd40`, `scd41` or `scd43`), otherwise `scd4x`. Older sensor firmware doesn't support the variant command.
- **Periodic mode:** started at init, giving a new reading about every 5 s. `read()` never blocks. It returns `[]` when there's no new data yet, which is normal on the first call after init. Call it no more often than every ~5 s if you want a reading every time.
- **Optional settings:** `temperature_offset=` (°C, ≥ 0, subtracted from the sensor's temperature; this replaces the sensor's built-in offset) and `altitude=` (metres above sea level). They're written to the sensor's RAM on every init and **never persisted**, so the caller's config stays the source of truth and the EEPROM isn't worn.
- **Self-healing:** after 3 failed reads in a row (I/O error or CRC failure) the driver re-runs its init. If that fails it logs an error and retries every 10th read. A sensor left in a bad state may need a **full power cycle**: a MicroPython soft reset doesn't remove its power.
- **Temperature:** in periodic mode it has been seen reading about 4 °C higher than single-shot on the same sensor, probably from self-heating or a nearby board. Prefer another sensor for room temperature unless you've calibrated it.
- Init takes about 500 ms (it has to stop periodic measurement first). The self-test command (10 s) is never used.

## Acknowledgements

Many thanks to Eugene Tkachenko ([@itkacher](https://www.youtube.com/@itkacher)), whose `itk_pico` MicroPython framework inspired the projects this package grew out of and gave them their start. kdmp now exists to make my own architectural choices.

## License

Apache 2.0. See `LICENSE`.
