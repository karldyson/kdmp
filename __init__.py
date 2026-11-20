# Author: Karl Dyson https://karld.blog
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# See the LICENSE file for the full text of the license.

"""kdmp: board-agnostic MicroPython helpers (Pico, ESP32, ...).

Subpackages:
    kdmp.log      levelled logging
    kdmp.sensors  sensor drivers sharing one reading interface

Nothing in this package creates pins or buses or assumes a particular
board: callers pass in machine.Pin / machine.I2C objects.
"""
