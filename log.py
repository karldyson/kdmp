# Author: Karl Dyson https://karld.blog
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# See the LICENSE file for the full text of the license.

"""Small levelled logger.

    from kdmp import log
    log.set_level("debug")          # or "info", "warning", "error", "off"
    _log = log.get("main")
    _log.info("reading %s = %.2f", sensor_id, value)

Prefer passing arguments (``_log.debug("t=%s", t)``) over f-strings:
the ``%`` formatting only happens when the level is enabled, so a
disabled debug line costs almost nothing. An f-string is always built
by the caller, even if the line is then dropped.

The level and the output function are global to the module, so one
``set_level()`` call at boot controls every logger.
"""

try:
	from time import ticks_ms
except ImportError:  # CPython, for host-side testing
	from time import monotonic as _mono

	def ticks_ms():
		return int(_mono() * 1000)

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
OFF = 100

_NAMES = {DEBUG: "DEBUG", INFO: "INFO", WARNING: "WARNING", ERROR: "ERROR"}
_BY_NAME = {"debug": DEBUG, "info": INFO, "warning": WARNING, "warn": WARNING, "error": ERROR, "off": OFF, "none": OFF}

_level = INFO
_output = print


def set_level(level):
	"""Set the global level from a constant or a name (case-insensitive).
	Unknown names fall back to INFO. Returns the numeric level."""
	global _level
	if isinstance(level, str):
		level = _BY_NAME.get(level.lower(), INFO)
	_level = level
	return _level


def get_level():
	return _level


def enabled(level):
	return level >= _level


def set_output(fn):
	"""Replace print as the sink. fn receives one formatted string."""
	global _output
	_output = fn


class Logger:
	def __init__(self, name):
		self.name = name

	def log(self, level, msg, *args):
		if level < _level:
			return
		if args:
			try:
				msg = msg % args
			except Exception:
				msg = "%s %r" % (msg, args)
		try:
			_output("[%d] %s %s: %s" % (ticks_ms(), _NAMES.get(level, level), self.name, msg))
		except Exception:
			# Logging must never take the caller down.
			pass

	def debug(self, msg, *args):
		self.log(DEBUG, msg, *args)

	def info(self, msg, *args):
		self.log(INFO, msg, *args)

	def warning(self, msg, *args):
		self.log(WARNING, msg, *args)

	def error(self, msg, *args):
		self.log(ERROR, msg, *args)


_loggers = {}


def get(name):
	"""Return the (shared) Logger for name."""
	lg = _loggers.get(name)
	if lg is None:
		lg = _loggers[name] = Logger(name)
	return lg
