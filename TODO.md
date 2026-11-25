# kdmp TODO

## UDP sending (migrate from pico-temperature `main.py` `multicast()`)

- Add a `kdmp.net` UDP sender that can send to **multicast and/or unicast** destinations.
- Each destination is switched on or off in config by a dict of its details, for example:
  ```python
  UDP = {
      "multicast": {"group": "239.0.0.1", "port": 9999, "ttl": 1},   # None/absent ⇒ off
      "unicast":   {"host": "192.0.2.10", "port": 9999},             # None/absent ⇒ off
  }
  ```
  - Consider allowing a list of unicast destinations.
- Keep the current behaviour: a send failure is logged and never raises into the main loop, and the socket is always closed.
- **Back-compat in consuming projects:** when there is no `UDP` setting, fall back to `MCAST_GROUP` / `UDP_PORT` as multicast-only.

## Later
- Migrate Wi-Fi connect/reconnect into `kdmp.net`. Keep the bounded timeouts and the watchdog feeding.
- Migrate DS18B20 into `kdmp.sensors.ds18b20`. Start one conversion for the whole bus, wait at least 750 ms, then read every probe. When no devices are found, log it and return an empty list instead of raising.
- SCD4x: optional forced recalibration (FRC) and automatic self-calibration (ASC) control. ASC is on by default, which suits rooms ventilated daily. Calibrate CO2 on the sensor, not with a software offset.
