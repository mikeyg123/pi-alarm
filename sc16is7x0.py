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

# Driver for SC16IS740/750/760 UART via I2C bus using wiring pi

import wiringpi2 as wp
import time

SLEEP_FOR_BITS = 20.0

THR = RHR = 0x00
IER = 0x01
IER_LSI = 0x04
IER_SLEEP = 0x10

FCR = IIR = 0x02
FCR_RX_TRIG_8 = 0x00
FCR_TX_TRIG_56 = 0x30
FCR_RESET_TX = 0x04
FCR_RESET_RX = 0x02
FCR_ENABLE_FIFO = 0x01

LCR = 0x03
LCR_ENABLE_DL = 0x80
LCR_ENABLE_EFRS = 0xBF
LCR_FORCE_PARITY = 0x20
LCR_EVEN_PARITY = 0x10
LCR_ENABLE_PARITY = 0x08
LCR_STOP_BIT = 0x04
LCR_LEN_MASK = 0x03

MCR = 0x04

LSR = 0x05
LSR_RX_DATA = 0x01
LSR_OVERRUN = 0x02
LSR_PARITY = 0x04
LSR_FRAME = 0x08
LSR_BREAK = 0x10
LSR_THR_EMPTY = 0x20
LSR_THR_TSR_EMPTY = 0x40
LSR_FIFO_ERR = 0x80

MSR = TCR = 0x06
SPR = TLR = 0x07
TXLVL = 0x08
RXLVL = 0x09
IODIR = 0x0A
IOSTATE = 0x0B
IEINTEN = 0x0C

IOC = 0x0E
EFCR = 0x0F
EFCR_RX_DISABLE = 0x02
EFCR_9BIT = 0x01

DLL = 0x00
DLH = 0x01

EFR = 0x02
EFR_SP_CHAR = 0x20

XON1 = 0x04
XON2 = 0x05
XOFF1 = 0x06
XOFF2 = 0x07

LCR_ENABLE_DL = 0x80
LCR_ENABLE_ER = 0xBF

class Uart:
	""" Driver for SC16IS740/750/760 UART via I2C bus"""
	
	def __init__(self, addr=0x48, xtal=14745600):
		self.addr = addr
		self.xtal = xtal
		self.fh = wp.wiringPiI2CSetup(self.addr)
		self.txSpaces = 0
		
	def setup(self, baud=1200, bits=8, parity="N", stops=1, enableRx=True, autoRS485=False, multidropAddr=None, debug=False):
		"""Reset and (re)Setup the UART
		Baud rates up to 80000 seem to work
		Bits 5, 6, 7 or 8
		Parity: O:odd, E:even, M:mark, S:space
		stops: 1, 2 for bits 6,7, or 8
		autoRS485 enables address detection described in section 9.3 of the datasheet - works with 8bits space parity.
		multidropAddr sets specific RS485 address detection described in section 9.3.2."""
		self.baud = baud
		self.parity = parity
		self.stops = stops
		self.autoRS485 = autoRS485
		self.multidropAddr = ord(multidropAddr[0]) if multidropAddr else None
		self.debug = debug
		
		# set the clock multiplier
		divisor = self.xtal / 16 / self.baud
		self.set(LCR, LCR_ENABLE_DL)
		self.set(DLH, divisor >> 8)
		self.set(DLL, divisor & 0xff)
		
		# set LCR
		self.lcr = 0x00
		if parity == "M" or parity == "S":
			self.lcr |= LCR_FORCE_PARITY
		if parity == "E" or parity == "S":
			self.lcr |= LCR_EVEN_PARITY
		if parity != "N":
			self.lcr |= LCR_ENABLE_PARITY
		if stops > 1:
			self.lcr |= LCR_STOP_BIT
		self.lcr |= ((bits - 5) & LCR_LEN_MASK)
		self.set(LCR, self.lcr)
		
		# set IER
		self.set(IER, IER_LSI)
		
		# set EFR & EFCR
		self.set(LCR, LCR_ENABLE_EFRS)
		self.set(EFCR, (EFCR_RX_DISABLE * (not enableRx)) | (EFCR_9BIT * self.autoRS485))
		if self.multidropAddr:
			self.set(EFR, EFR_SP_CHAR)
			self.set(XOFF2, self.multidropAddr)
		self.set(LCR, self.lcr)
		
		# set FCR - reset and enable fifo (tx chars disabled above)
		self.set(FCR, FCR_RX_TRIG_8 | FCR_TX_TRIG_56 | FCR_RESET_TX | FCR_RESET_RX | FCR_ENABLE_FIFO)

		# set MCR (not using MCR or TCR/TLR)
		self.set(MCR, 0x00)
		
		# set IOC
		self.set(IOC, 0x00)
		
		
	def set(self, reg, val):
		"""Directly set value of a register
		- note this can put the UART into an unknown state"""
		if self.debug:
			print("set register {:#x} -> 0b{:0>8b} {}".format(reg, val, repr(chr(val))))
		wp.wiringPiI2CWriteReg8(self.fh, reg << 3, val)
		
	def get(self, reg):
		"""Directly read the value of a register"""
		val = wp.wiringPiI2CReadReg8(self.fh, reg << 3)
		if self.debug:
			print("get register {:#x} <- 0b{:0>8b} {}".format(reg, val, repr(chr(val))))
		return val

	def resetTx(self):
		self.set(FCR, FCR_RX_TRIG_8 | FCR_TX_TRIG_56 | FCR_RESET_TX | FCR_ENABLE_FIFO)
		
	def writeChar(self, c):
		"""write a single character"""
		if self.debug:
			print(repr("writing " + c))

		if self.txSpaces <= 0:
			self.txSpaces = self.get(TXLVL)
			if self.txSpaces <= 0:
				# sleep for a little more than the time required to send a char
				s = time.time()
				time.sleep(SLEEP_FOR_BITS / self.baud)
				self.txSpaces = self.get(TXLVL)
				if self.txSpaces <= 0:
					# still no room in buffer
					return 0
		self.set(THR, ord(c))
		self.txSpaces -= 1
		return 1
		
	def writeAddr(self, c):
		"""Write a single character with the parity forced to 1"""
		if self.debug:
			print("Writing addr char")
		# wait for the tx buffer to empty
		self.waitForEmptyTx()
		# set parity Mark
		self.set(LCR, self.lcr & ~LCR_EVEN_PARITY)
		self.resetTx()
		# write char
		self.writeChar(c)
		# wait for char to be sent
		self.waitForEmptyTx()
		# set parity back
		self.set(LCR, self.lcr)
		self.resetTx()

	def waitForEmptyTx(self):
		""" Waits (polling) for the tx buffer to empty
		gives up if the buffer doesn't go down as fast as it should"""
		waited = 0 
		txlvl = -1
		while not self.get(LSR) & LSR_THR_TSR_EMPTY:
			newTxlvl = self.get(TXLVL)
			if newTxlvl != txlvl:
				# level going down, wait longer
				waited = 0
			elif waited > SLEEP_FOR_BITS:
				# it got stuck, give up
				break
			time.sleep(1.0 / self.baud)
			waited += 1
			
	def write(self, string):
		"""Write data to transmit, 
		stops if there was any significant delay sending
		returns the number of chars sent"""
		t = 0
		for c in string:
			w = self.writeChar(c)
			if (0 == w):
				# still blocked
				return t
			t += w
		return t
	
		
	def writeAddrMsg(self, s):
		"""Transmit a string with the first char parity forced to 1 to mark it
		as an RS485 address byte"""
		self.writeAddr(s[0])
		self.write(s[1:])
		
	def enableRx(self):
		self.set(LCR, LCR_ENABLE_EFRS)
		self.set(EFCR, (EFCR_9BIT * self.autoRS485))
		self.set(LCR, self.lcr)
		
	def disableRx(self):
		self.set(LCR, LCR_ENABLE_EFRS)
		self.set(EFCR, EFCR_RX_DISABLE | (EFCR_9BIT * self.autoRS485))
		self.set(LCR, self.lcr)

	def resetRx(self):
		self.set(FCR, FCR_RX_8 | FCR_TX_56 | FCR_RESET_RX | FCR_ENABLE_FIFO)

	def readChar(self, ignoreParityErr=False):
		"""read a char - by default won't read the next char if there was a parity error
		ignoreParityErr - read the next char whatever
		Note that (contrary to documentation) reading the LSR clears the 
		error so a subsequent read will not see the previous parity error"""
		self.lsr = self.get(LSR)
		# if no data, wait a bit
		if (not self.lsr & LSR_RX_DATA):
			time.sleep(SLEEP_FOR_BITS / self.baud)
			self.lsr = self.get(LSR)
			if (not self.lsr & LSR_RX_DATA):
				# still no data - give up
				return ''
		parityErr = bool(self.lsr & LSR_PARITY)
		if ignoreParityErr or not parityErr:
			c = chr(self.get(RHR))
			if self.debug and parityErr:
				print("parity")
			return c
		return ''
		
	def readMsg(self, n=-1):
		"""Read an RS485 addressed message allowing for a parity error
		on the first char and stopping at the next error or when there's a significant gap in the data stream"""
		return self.readChar(ignoreParityErr = True) + self.read(n - 1)
				
	def read(self, n=-1, ignoreParityErr=False):
		"""Reads specified number of chars or until there's a parity error (addr)
		or a pause in the data stream"""
		s = ""
		while (n != 0):
			c = self.readChar(ignoreParityErr = ignoreParityErr)
			if not len(c):
				# nothing to read
				break
			if self.lsr & (LSR_BREAK | LSR_FRAME):
				# skip breaks & framing errors
				continue
			s += c
			if n > 0:
				n -= 1
		return s

	def setIODir(self, v):
		"""Set direction of GPIO pins (SC16IS750/760 only)"""
		self.set(IODIR, v)

	def setIOState(self, v):
		"""Set state of GPIO pins (SC16IS750/760 only)"""
		self.set(IOSTATE, v)

	def getIOState(self):
		"""Get state of GPIO pins (SC16IS750/760 only)"""
		self.get(IOSTATE)
