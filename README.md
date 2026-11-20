# kdmp

Reusable MicroPython helpers that don't depend on a particular board. They are meant to run on the Raspberry Pi Pico / Pico 2 W, ESP32 and similar boards. This repo is designed to be included in projects as a git submodule mounted at `kdmp/`, so the code imports as `kdmp.<module>`.

## Contents

| Module | Purpose |
|---|---|
| `kdmp.log` | Levelled logger (`debug`/`info`/`warning`/`error`/`off`) with lazy formatting |
| `kdmp.sensors.base` | The driver interface that every sensor implements, plus shared helpers |
| `kdmp.sensors.sht3x` | Sensirion SHT30/31/35 temperature and humidity sensors over I2C |

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

## Acknowledgements

Many thanks to Eugene Tkachenko ([@itkacher](https://www.youtube.com/@itkacher)), whose `itk_pico` MicroPython framework inspired the projects this package grew out of and gave them their start. kdmp now exists to make my own architectural choices.

## License

Apache 2.0. See `LICENSE`.
