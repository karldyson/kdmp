# Author: Karl Dyson https://karld.blog
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# See the LICENSE file for the full text of the license.

"""Generic sensor driver interface and shared helpers.

A driver instance may represent several physical sensors (e.g. a 1-Wire
bus with N probes), so:

- ``ids()`` returns the physical IDs (strings) found at init.
- ``read()`` returns a list of readings, one dict per physical sensor:

      {"sensor": "20e80802", "model": "sht30",
       "temperature": 20.92, "humidity": 49.9}

  Known quantities: ``temperature`` (C, float), ``humidity`` (%RH,
  float), ``co2`` (ppm, int). Quantities a sensor doesn't measure are
  left out (never None).
  A sensor whose reading failed is left out of the list.
- ``read()`` must never raise: log the problem and return what you have.
- ``quantities`` (class attribute) is a tuple of the quantity names the
  driver measures, so callers know what a sensor provides before any
  read (e.g. to check which sensor supplies which value).

Drivers take bus/pin objects from the caller and never create them.
"""

import time
from kdmp import log as _logmod


class SensorDriver:
	model = "unknown"
	quantities = ()

	def __init__(self, log=None):
		self.log = log if log is not None else _logmod.get(self.model)

	def ids(self):
		return []

	def read(self):
		return []


def position_id(bus, addr):
	"""Fallback ID for a sensor that can't report a serial.

	NOTE: this identifies the *position* on this unit (board + bus +
	address), not the physical probe; swapping the probe keeps the ID.
	"""
	try:
		import machine
		import binascii
		board = binascii.hexlify(machine.unique_id()).decode()
	except Exception:
		board = "unknown"
	return "%s-i2c%s-%02x" % (board, bus, addr)


def sleep_ms(ms):
	"""time.sleep_ms on MicroPython, with a CPython fallback for host tests."""
	try:
		time.sleep_ms(ms)
	except AttributeError:  # CPython
		time.sleep(ms / 1000)


def crc8(data):
	"""Sensirion CRC-8 (SHT3x, SCD4x, ...): polynomial 0x31, init 0xFF."""
	crc = 0xFF
	for b in data:
		crc ^= b
		for _ in range(8):
			if crc & 0x80:
				crc = ((crc << 1) ^ 0x31) & 0xFF
			else:
				crc = (crc << 1) & 0xFF
	return crc
