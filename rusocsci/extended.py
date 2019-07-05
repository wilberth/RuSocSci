#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RuSocSci module for the BITSI extended buttonbox

Copyright (C) 2013-2019 Wilbert van Ham, Radboud University Nijmegen
Distributed under the terms of the GNU General Public License (GPL) version 3 or newer.
"""
import sys
import time
import logging
from . import utils, buttonbox # p23

class Extended(buttonbox.Buttonbox):
	"""
	Object that connects tot RuSocSci buttonbox in extended mode. Typical usage::

		from rusocsci import extended

		bb = extended.Extended() # connect to last inserted buttonbox

		print("Press any key")
		l = bb.waitKeys(10)
		if l:
			print("key pressed: {}".format(l[0]))
		else:
			print("no key pressed.")

	or for non-blocking input (using the Python 3 print function)::

		import time, sys
		from rusocsci import buttonbox

		bb = buttonbox.Buttonbox() # connect to last inserted buttonbox

		print("Press any key")
		while not len(bb.getKeys()): # while there is no input
			print(".", end='')
			sys.stdout.flush()
			time.sleep(1)

	"""
	def __init__(self, id=0, port=None):
		self._device, idString = utils.open(utils.getPort(id, port))
		idStringCorrect = "BITSI_extend mode, Ready!"
		if not self._device:
			logging.error("No BITSI extended buttonbox connected.")
		elif idString[:len(idStringCorrect)] == idStringCorrect:
			logging.debug("Device is a BITSI extended buttonbox: %s", idString)
		else:
			logging.info("Device did not identify as a BITSI extended buttonbox: %s", idString)
		self.calibratedSound = False
		self.calibratedVoice = False

	def send(self, val):
		"""
		Set buttonbox LEDs to a certain pattern
		"""
		if self._device is None:
			raise Exception("No buttonbox connected")
		#self._device.write(bytes((val,))) # p23

		if sys.version_info >= (3, 0): #0.8.3
			self._device.write(bytes([val]))
		else:
			self._device.write(chr(val))

	def setLeds(self, leds=None, val=None):
		"""
		connect leds to signals output by computer
		"""
		if leds is None:
			leds = [False, False, False, False, False, False, False, False]
		if val is None:
			val = 0
			for i in range(8):
				if len(leds) > i:
					if leds[i]:
						val += 1<<i
				else:
					break
		self.send(ord('L'))
		self.send(ord('O'))
		self.send(val)

	def sendMarker(self, markers=None, val=None):
		"""
		send marker to buttonbox output
		"""
		if markers is None:
			markers = [False, False, False, False, False, False, False, False]
		if val is None:
			val = 0
			for i in range(8):
				if len(markers) > i:
					if markers[i]:
						val += 1<<i
				else:
					break
		self.send(ord('M'))
		self.send(val)

	def calibrateSound(self):
		"""
		define silence as the volume in the next second
		"""
		self.send(ord('C')) # calibrate sound
		self.send(ord('S'))
		time.sleep(1) # make sure to be silent during the calibration
		self.calibratedSound = True

	def waitSound(self, maxWait=float("inf"), flush=True, buttonList='S'):
		"""
		wait till sound is detected
		"""
		if not self.calibratedSound:
			logging.debug("calibrating sound, wait 1 s.")
			self.calibrateSound()
		if flush:
			self.clearEvents() # flush possible awaiting sound events
		self.send(ord('D')) # detect sound
		self.send(ord('S'))
		return self.waitButtons(buttonList=buttonList, flush=False, maxWait=maxWait)

	def calibrateVoice(self):
		"""
		define silence as the volume in the next second
		"""
		self.send(ord('C')) # calibrate
		self.send(ord('V'))
		time.sleep(1) # make sure to be silent during the calibration
		self.calibratedVoice = True

	def waitVoice(self, maxWait=float("inf"), flush=True, buttonList='V'):
		"""
		wait till sound is detected
		"""
		if not self.calibratedVoice:
			logging.debug("calibrating voice, wait 1 s.")
			self.calibrateVoice()
		if flush:
			self.clearEvents() # flush possible awaiting sound events
		self.send(ord('D')) # detect sound
		self.send(ord('V'))
		return self.waitButtons(buttonList=buttonList, flush=False, maxWait=maxWait)
