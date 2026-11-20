# Author: Karl Dyson https://karld.blog
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# See the LICENSE file for the full text of the license.

"""Sensirion SHT3x (SHT30/31/35) temperature + humidity over I2C.

    from machine import I2C, Pin
    from kdmp.sensors.sht3x import SHT3x
    i2c = I2C(1, sda=Pin(26), scl=Pin(27), freq=100000)
    sht = SHT3x(i2c, addr=0x44, bus=1)
    sht.read()  # [{"sensor": "20e80802", "model": "sht30", "temperature": ..., "humidity": ...}]

Uses single-shot, high-repeatability measurements without clock
stretching. Every word is CRC-checked; a bad value is never returned.
"""

import time
from kdmp.sensors.base import SensorDriver, position_id

_CMD_MEASURE = b"\x24\x00"   # single shot, high repeatability, no clock stretching
_CMD_SERIAL = b"\x36\x82"    # read serial number, no clock stretching
_MEASURE_WAIT_MS = 20        # datasheet max 15ms for high repeatability
_SERIAL_WAIT_MS = 10


def _sleep_ms(ms):
	try:
		time.sleep_ms(ms)
	except AttributeError:  # CPython
		time.sleep(ms / 1000)


def crc8(data):
	"""Sensirion CRC-8: polynomial 0x31, init 0xFF."""
	crc = 0xFF
	for b in data:
		crc ^= b
		for _ in range(8):
			if crc & 0x80:
				crc = ((crc << 1) ^ 0x31) & 0xFF
			else:
				crc = (crc << 1) & 0xFF
	return crc


def _words(buf):
	"""Split 6 bytes (word, crc, word, crc) into two ints, or None on CRC failure."""
	if len(buf) != 6:
		return None
	if crc8(buf[0:2]) != buf[2] or crc8(buf[3:5]) != buf[5]:
		return None
	return (buf[0] << 8) | buf[1], (buf[3] << 8) | buf[4]


class SHT3x(SensorDriver):
	def __init__(self, i2c, addr=0x44, bus=None, model="sht30", log=None):
		self.model = model
		super().__init__(log)
		self._i2c = i2c
		self._addr = addr
		self._bus = bus
		serial = self._read_serial()
		if serial is not None:
			self._id = serial
			self.log.info("SHT3x at 0x%02x: serial %s", addr, serial)
		else:
			self._id = position_id(bus, addr)
			self.log.warning("SHT3x at 0x%02x: no serial, using position ID %s", addr, self._id)

	def _transact(self, cmd, wait_ms):
		self._i2c.writeto(self._addr, cmd)
		_sleep_ms(wait_ms)
		return _words(self._i2c.readfrom(self._addr, 6))

	def _read_serial(self):
		try:
			w = self._transact(_CMD_SERIAL, _SERIAL_WAIT_MS)
		except OSError as e:
			self.log.warning("SHT3x serial read failed: %s", e)
			return None
		if w is None:
			self.log.warning("SHT3x serial read: CRC mismatch")
			return None
		return "%08x" % ((w[0] << 16) | w[1])

	def ids(self):
		return [self._id]

	def read(self):
		for attempt in (1, 2):
			try:
				w = self._transact(_CMD_MEASURE, _MEASURE_WAIT_MS)
			except OSError as e:
				self.log.warning("SHT3x %s read attempt %d: %s", self._id, attempt, e)
				continue
			if w is None:
				self.log.warning("SHT3x %s read attempt %d: CRC mismatch", self._id, attempt)
				continue
			t = round(-45 + 175 * w[0] / 65535, 2)
			rh = round(100 * w[1] / 65535, 2)
			self.log.debug("SHT3x %s: %.2f C %.2f %%RH", self._id, t, rh)
			return [{"sensor": self._id, "model": self.model, "temperature": t, "humidity": rh}]
		self.log.error("SHT3x %s: no valid reading, skipping", self._id)
		return []
