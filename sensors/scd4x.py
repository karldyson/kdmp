# Author: Karl Dyson https://karld.blog
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# See the LICENSE file for the full text of the license.

"""Sensirion SCD4x (SCD40/41/43) CO2 + temperature + humidity over I2C.

    from machine import I2C, Pin
    from kdmp.sensors.scd4x import SCD4x
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
    scd = SCD4x(i2c, addr=0x62, bus=0)
    scd.read()  # [{"sensor": "1cab65073b57", "model": "scd41", "co2": 465, "temperature": 23.15, "humidity": 38.8}]

Runs in periodic measurement mode (a new reading every ~5 s), started at
init, so read() never blocks: it checks data-ready and returns [] when
there's nothing new yet (normal for the first call after init).

While periodic measurement is running the sensor only accepts
read_measurement, get_data_ready_status, stop_periodic_measurement and
the ambient-pressure commands; anything else is undefined behaviour.
Every other command here is sent only after stop_periodic_measurement.

Configured temperature offset / altitude are written to the sensor's RAM
at each init and never persisted, so config stays the source of truth
and the EEPROM isn't worn.
"""

from kdmp.sensors.base import SensorDriver, position_id, crc8, sleep_ms

_CMD_STOP_PERIODIC = 0x3F86
_CMD_START_PERIODIC = 0x21B1
_CMD_DATA_READY = 0xE4B8
_CMD_READ_MEASUREMENT = 0xEC05
_CMD_SERIAL = 0x3682
_CMD_VARIANT = 0x202F
_CMD_SET_TEMP_OFFSET = 0x241D
_CMD_SET_ALTITUDE = 0x2427

_STOP_WAIT_MS = 500
_CMD_WAIT_MS = 1

# get_sensor_variant: top 4 bits of the word. SCD41 verified on hardware;
# check the others against the current datasheet revision.
_VARIANTS = {0x0: "scd40", 0x1: "scd41", 0x5: "scd43"}

_REINIT_AFTER = 3     # consecutive failed reads before re-running init
_REINIT_EVERY = 10    # then retry init on every Nth failed read


class SCD4x(SensorDriver):
	quantities = ("co2", "temperature", "humidity")

	def __init__(self, i2c, addr=0x62, bus=None, model=None, log=None, temperature_offset=None, altitude=None):
		self.model = model or "scd4x"
		super().__init__(log)
		self._i2c = i2c
		self._addr = addr
		self._bus = bus
		self._temperature_offset = temperature_offset
		self._altitude = altitude
		self._serial = None
		self._variant = None
		self._running = False
		self._fails = 0

		self._init()

		if self._serial is not None:
			self._id = self._serial
		else:
			self._id = position_id(bus, addr)
			self.log.warning("SCD4x at 0x%02x: no serial, using position ID %s", addr, self._id)
		if model is None and self._variant is not None:
			self.model = self._variant
		self.log.info("SCD4x at 0x%02x: ID %s, model %s, %s", addr, self._id, self.model,
			"measuring" if self._running else "NOT measuring (will retry)")

	# --- low-level I2C -------------------------------------------------

	def _cmd(self, code, wait_ms=_CMD_WAIT_MS):
		self._i2c.writeto(self._addr, bytes([code >> 8, code & 0xFF]))
		sleep_ms(wait_ms)

	def _write_word(self, code, value, wait_ms=_CMD_WAIT_MS):
		w = bytes([value >> 8, value & 0xFF])
		self._i2c.writeto(self._addr, bytes([code >> 8, code & 0xFF]) + w + bytes([crc8(w)]))
		sleep_ms(wait_ms)

	def _read_words(self, n):
		"""n CRC-checked 16-bit words, or None if any CRC fails."""
		buf = self._i2c.readfrom(self._addr, n * 3)
		if len(buf) != n * 3:
			return None
		words = []
		for i in range(0, n * 3, 3):
			if crc8(buf[i:i + 2]) != buf[i + 2]:
				return None
			words.append((buf[i] << 8) | buf[i + 1])
		return words

	# --- init ----------------------------------------------------------

	def _init(self):
		"""Stop, identify, configure and start periodic measurement.

		Safe to call at any time (stop_periodic is always allowed). Takes
		~500 ms. Returns True if periodic measurement was started.
		"""
		self._running = False

		try:
			self._cmd(_CMD_STOP_PERIODIC, _STOP_WAIT_MS)
		except OSError as e:
			# NACK is normal if it was already idle; carry on
			self.log.debug("SCD4x stop_periodic: %s (may already be idle)", e)
			sleep_ms(_STOP_WAIT_MS)

		try:
			self._cmd(_CMD_SERIAL)
			w = self._read_words(3)
			if w is None:
				self.log.warning("SCD4x serial read: CRC mismatch")
			elif self._serial is None:
				self._serial = "%04x%04x%04x" % (w[0], w[1], w[2])
		except OSError as e:
			self.log.warning("SCD4x serial read failed: %s", e)

		try:
			self._cmd(_CMD_VARIANT)
			w = self._read_words(1)
			if w is not None:
				self._variant = _VARIANTS.get(w[0] >> 12)
				self.log.debug("SCD4x variant word 0x%04x -> %s", w[0], self._variant)
		except OSError as e:
			# not supported by older sensor firmware
			self.log.debug("SCD4x get_sensor_variant not supported: %s", e)

		try:
			if self._temperature_offset is not None:
				word = round(self._temperature_offset * 65535 / 175)
				if 0 <= word <= 0xFFFF:
					self._write_word(_CMD_SET_TEMP_OFFSET, word)
					self.log.info("SCD4x temperature offset set to %s C", self._temperature_offset)
				else:
					self.log.warning("SCD4x temperature offset %s out of range, not set", self._temperature_offset)
			if self._altitude is not None:
				alt = int(self._altitude)
				if 0 <= alt <= 0xFFFF:
					self._write_word(_CMD_SET_ALTITUDE, alt)
					self.log.info("SCD4x altitude set to %s m", alt)
				else:
					self.log.warning("SCD4x altitude %s out of range, not set", self._altitude)
		except OSError as e:
			self.log.warning("SCD4x settings write failed: %s", e)

		try:
			self._cmd(_CMD_START_PERIODIC)
		except OSError as e:
			self.log.warning("SCD4x start_periodic failed: %s", e)
			return False
		self._running = True
		return True

	# --- interface -----------------------------------------------------

	def ids(self):
		return [self._id]

	def _read_once(self):
		"""Returns a reading dict, "notready", or None on CRC failure. May raise OSError."""
		self._cmd(_CMD_DATA_READY)
		w = self._read_words(1)
		if w is None:
			return None
		if not w[0] & 0x07FF:
			return "notready"
		self._cmd(_CMD_READ_MEASUREMENT)
		w = self._read_words(3)
		if w is None:
			return None
		return {
			"sensor": self._id,
			"model": self.model,
			"co2": w[0],
			"temperature": round(-45 + 175 * w[1] / 65535, 2),
			"humidity": round(100 * w[2] / 65535, 2),
		}

	def read(self):
		if self._running:
			try:
				r = self._read_once()
			except Exception as e:  # OSError (NACK) normally; read() must never raise
				self.log.warning("SCD4x %s read failed: %s", self._id, e)
				r = None
			else:
				if r is None:
					self.log.warning("SCD4x %s read: CRC mismatch", self._id)
			if r == "notready":
				self.log.debug("SCD4x %s: no new data yet", self._id)
				return []
			if r is not None:
				if self._fails >= _REINIT_AFTER:
					self.log.info("SCD4x %s recovered", self._id)
				self._fails = 0
				self.log.debug("SCD4x %s: %d ppm %.2f C %.2f %%RH", self._id, r["co2"], r["temperature"], r["humidity"])
				return [r]

		self._fails += 1
		n = self._fails - _REINIT_AFTER
		if n >= 0 and n % _REINIT_EVERY == 0:
			self.log.warning("SCD4x %s: %d failed reads, re-initialising", self._id, self._fails)
			try:
				ok = self._init()
			except Exception as e:  # read() must never raise
				self.log.warning("SCD4x %s re-init error: %s", self._id, e)
				ok = False
			if not ok:
				self.log.error("SCD4x %s unresponsive; a full power cycle may be needed "
					"(a soft reset does not remove its power). Retrying every %d reads.",
					self._id, _REINIT_EVERY)
		return []
