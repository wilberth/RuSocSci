#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RuSocSci module for the red joystick

Copyright (C) 2013-2019 Wilbert van Ham, Radboud University Nijmegen
Distributed under the terms of the GNU General Public License (GPL) version 3 or newer.

Known issues:
    - All usb2serial devices are detected. The list of joysticks therefore also contains
      buttonboxes.

"""
import sys, serial, time, os, re, logging, struct
from . import utils

# our buttonbox and joystick have id 0403:6001 from its UART IC
# make sure you have the pyusb module installed
# for MS Windows you may need this: http://sourceforge.net/apps/trac/libusb-win32/wiki
def getNumJoysticks():
	""""
	Return a count of the number of joysticks available. 
	This really returns a count of all usb to serial devices
	"""
	return len(utils.serialList())

class Joystick():
	"""
	Typical usage::

		from rusocsci import joystick
		import time

		nJoys = joystick.getNumJoysticks() # to check if we have any
		id=0
		joy = joystick.Joystick(id)#id must be <= nJoys-1

		while True:#while presenting stimuli
			x = joy.getX()
			time.sleep(1)
	"""
	def __init__(self, id=0, port=None):
		self.x = 126 # angle range is [51..201]
		[self._device, idString] = utils.open(utils.getPort(id, port))

		if idString == "joystick streaming angle, Ready!":
			logging.debug("Device is a joystick ({}): {}".format(len(idString), idString))
		else:
			logging.error("Device is NOT a joystick ({}): {}".format(len(idString), idString))

	def __del__(self):
		if self._device:
			self._device.close()

	def getNumHats(self):
		"Get the number of hats on this joystick"
		return 0
	def getX(self):
		"Returns the value on the X axis (equivalent to joystick.getAxis(0))"
		if self._device == None:
			logging.error("Joystick not initialized")
			return -1
		self._device.timeout = 0
		c = self._device.read()
		nBytes = 0
		while len(c) != 0:
			self.x = struct.unpack('B', c)[0]
			nBytes+=1
			c = self._device.read()
		logging.debug("read {} bytes, ending in {}".format(nBytes, self.x))
		return self.x

	def getAllAxes(self):
		"""
		Get a list of all current axis values
		"""
		return [self.getX()]
	def getNumAxes(self):
		"""
		Returns the number of joystick axes found
		"""
		return 1
	def getAxis(self, axisId):
		"""
		Get the value of an axis by an integer id (from 0 to number of axes-1)
		"""
		return self.getX()
	
	def clearEvents():
		if _device == None:
			event.flushInput(keyboard)
		else:
			self._device.flushInput()
		
