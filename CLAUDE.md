# kdmp — Claude Context

Reusable, board-agnostic MicroPython package (Pico/Pico 2 W, ESP32-S3, ...). Consumed by projects as a git submodule mounted at `kdmp/`; the repo root *is* the package (`import kdmp.sensors.sht3x`). Networking (Wi-Fi/UDP) will move here next.

## Background: itk_pico
The author's projects were originally built on itk_pico, Eugene Tkachenko's MicroPython framework for the Pico (https://www.youtube.com/@itkacher). The author's copy is at https://github.com/karldyson/itk_pico. With thanks to Eugene: itk_pico was the inspiration and the starting point for these projects.

The author is moving to kdmp for two reasons of their own:
- **Broader hardware:** kdmp has to run on boards other than the Pico, such as the ESP32-S3.
- **Architectural control:** the author wants to set their own conventions, such as the caller passing in pins and buses, a common sensor-reading interface, levelled logging, etc.

This is about the author's own needs and design choices. It says nothing about the quality of itk_pico. Code is migrated by clean rewrite. Any code copied from itk_pico keeps its Apache 2.0 notice and attribution.

Edits happen in a standalone clone of this repo, never in a consuming project's submodule checkout: change, commit and push here, then bump the submodule pointer in the consuming project.

## Rules
- Never create `machine.Pin`/`machine.I2C` etc. inside the package — callers pass them in. No board-specific assumptions.
- Never import `itk_pico`.
- Log via `kdmp.log.get("<name>")` with `%`-style args (lazy formatting); drivers accept an optional `log=` override.
- Sensor drivers subclass `kdmp.sensors.base.SensorDriver`: `ids()` → list of ID strings, `read()` → list of reading dicts; `read()` never raises, omits unmeasured quantities and failed sensors. Each driver sets the class attribute `quantities` to the tuple of quantity names it measures (`temperature`, `humidity`, `co2`).
- Shared helpers live in `sensors/base.py` (`crc8` for Sensirion parts, `sleep_ms`, `position_id`); don't duplicate them in drivers.
- Every wait inside a driver must be short (≤500 ms) so callers can keep feeding a hardware watchdog.
- Name files after a sensor only when dedicated to it.
- Keep code importable under CPython too where cheap (guarded `time.sleep_ms`/`ticks_ms`) so it can be syntax/unit-checked on a host.
- Tabs for indentation (matches consuming projects).

## SCD4x gotchas
- While periodic measurement is running, send **only** `read_measurement`, `get_data_ready_status`, `stop_periodic_measurement` or the ambient-pressure commands. Anything else is undefined (it looked like resets in testing). Stop first (500 ms) for everything else.
- Never send a command while the previous one is still executing; respect each command's wait time.
- Never run `perform_self_test` (10 s) in the driver; it would trip a caller's watchdog.
- Don't call `persist_settings`: offset/altitude are written to RAM at each init.
- A sensor in an odd state may NACK everything until fully power-cycled; a soft reset doesn't power it down. The driver re-inits after 3 failures, then every 10th, and logs an error saying so.

## Machine-specific notes (private, not committed)

@~/.claude/local/kdmp.md
