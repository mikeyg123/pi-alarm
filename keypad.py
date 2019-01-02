# Copyright (C) 2015 Mike Gould
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 2.1, as
# published by the Free Software Foundation.  This program is
# distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.


# Interface to the alarm keypad(s)
# requires a serial connection 
# Allows you to:
# display message
# set lights
# subscribe to keypresses

import functools
import wiringpi2 as wp


class Keypad:
	"""Interface to the alarm keypad
	requires a serial connection
	allows you to subscribe to keypresses, set leds, write to lcd"""
	
	ADDR_KEY = "K"
	ADDR_LED = "P"
	ADDR_LCD = "L"
	
	KEY_BELL = ":"
	KEY_OMIT = ";"
	KEY_X = "<"
	KEY_P = "="
	KEY_Y = ">"
	KEY_UP = "?"
	KEY_SOS = "\xaa"
	
	LCD_CLEAR = "\f"
	LCD_CMD = "\x04"
	LCD_LINE1 = 0x80
	LCD_LINE2 = 0xc0
	
	LED_UNSET = 0x01
	LED_TAMP = 0x00
	LED_SOS = 0x00
	LED_PWR = 0x0a
	
	def __init__(self, connection):
		self.connection = connection
		
	def write(self, s):
		m = s + chr(self.checksum(s))
		print("Writing LCD: '" + m + "'")
		self.connection.writeAddrMsg(m)

	def checksum(self, s):
		return functools.reduce(lambda a, b: a + ord(b), s, 0) & 0xff
		
	def writeLcd(self, s):
		self.write(self.ADDR_LCD + chr(len(s)) + s)

	def setLeds(self, zones, leds):
		self.write(self.ADDR_LED + chr(zones) + chr(leds))
		
	def readKey(self):
		msg = self.connection.readMsg(3)
		return msg[1] if len(msg) >= 3 and msg[0] == self.ADDR_KEY and self.checksum(msg[:-1]) == ord(msg[-1]) else None

		



