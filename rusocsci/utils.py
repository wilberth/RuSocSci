#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RuSocSci module for utilities, like listing USB to serial devices and connecting to them.

# Copyright (C) 2013-2019 Wilbert van Ham, Radboud University Nijmegen
# Distributed under the terms of the GNU General Public License (GPL) version 3 or newer.

Known issues:
    - All usb to serial devices are detected. The list of devices therefore contains
      joysticks, buttonboxes and other usb to serial devices.

"""
import sys, serial, time, os, re, logging, struct

TIMEOUT = 6.0
if sys.platform == "win32":
	if sys.version_info >= (3, 0):
		import winreg as _winreg
	else:
		import _winreg

class HideStderr(object):
	'''
	A context manager that blocks stderr for its scope, usage::

		from rusocsci import utils
		import os
		with utils.HideStderr():
			os.system('ls noexistentfile') # error will not show

	'''

	def __init__(self, *args, **kw):
		sys.stderr.flush()
		self._origstderr = sys.stderr
		self._oldstderr_fno = os.dup(sys.stderr.fileno())
		self._devnull = os.open(os.devnull, os.O_WRONLY)

	def __enter__(self):
		self._newstderr = os.dup(2)
		os.dup2(self._devnull, 2)
		os.close(self._devnull)
		sys.stderr = os.fdopen(self._newstderr, 'w')

	def __exit__(self, exc_type, exc_val, exc_tb):
		sys.stderr = self._origstderr
		sys.stderr.flush()
		os.dup2(self._oldstderr_fno, 2)
		os.close(self._oldstderr_fno)
		
class HideStdout(object):
	'''
	A context manager that blocks stdout for its scope, usage::

		from rusocsci import utils
		import os
		with utils.HideStdout():
			os.system('ls -l') # output will not show
	'''

	def __init__(self, *args, **kw):
		sys.stdout.flush()
		self._origstdout = sys.stdout
		self._oldstdout_fno = os.dup(sys.stdout.fileno())
		self._devnull = os.open(os.devnull, os.O_WRONLY)

	def __enter__(self):
		self._newstdout = os.dup(1)
		os.dup2(self._devnull, 1)
		os.close(self._devnull)
		sys.stdout = os.fdopen(self._newstdout, 'w')

	def __exit__(self, exc_type, exc_val, exc_tb):
		sys.stdout = self._origstdout
		sys.stdout.flush()
		os.dup2(self._oldstdout_fno, 1)
		os.close(self._oldstdout_fno)


# our buttonbox and joystick have id 0403:6001 from its UART IC
# make sure you have the pyusb module installed
# for MS Windows you may need this: http://sourceforge.net/apps/trac/libusb-win32/wiki
# FTDIBUS
def _winList(service, bus=None, suffix=None):
	""""
	Helper for windows for serialList function
	"""
	try:
		# find number of FTDI USB serial devices attached
		reg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
		keyString = r"SYSTEM\CurrentControlSet\services""\\" + service + r"\Enum"
		key = _winreg.CreateKeyEx(reg, keyString, 0, _winreg.KEY_READ)
		count = _winreg.QueryValueEx(key, "Count")[0]
	except Exception as e:
		logging.info("Could not create service key string: {}".format(keyString))
		return []
	
	if count == 0:
		logging.debug("No "+ service +" USB serial device connected.")
	if count > 1:
		logging.debug("Multiple "+ service +"  USB serial connected, last connected is first in list.")
		
	devices = []
	for i in range(count-1, -1, -1):
		value = _winreg.QueryValueEx(key, str(i))[0]
		devices.append(value)
	logging.debug("USB serial devices ({}): {}".format(service, devices))
	
	# find the corresponding serial ports
	ports = []
	for device in devices:
		#device is something like: ur"USB\VID_0403&PID_6001\AH01L3OL" or "USB\VID_2341&PID_0043\6493433313535141D0B2"
		id = device[22:]
		# find port, the following line gives an error in windows without administrative priviliges
		try:
			if bus:
				keyString = r"SYSTEM\CurrentControlSet\Enum""\\" + bus + id + suffix + r"\Device Parameters"
			else:
				keyString = r"SYSTEM\CurrentControlSet\Enum""\\" + device + r"\Device Parameters"
			key = _winreg.CreateKey(reg, keyString)
		except Exception as e:
			logging.info("Could not create device key string: {}".format(keyString))
			return []
		try:
			value = _winreg.QueryValueEx(key, "PortName")[0]
			ports.append(value)
		except Exception as e:
			logging.info("Could not find USB serial device, no value for PortName: {}\n".format(e))
	return [s.encode('ascii', 'ignore') for s in ports]

def serialList():
	"""
	Get a list of USB to serial devices connected. The returned list is that of the serial ports.
	"""
	if sys.platform == "win32":
		ports = _winList("FTDIBUS", r"FTDIBUS\VID_0403+PID_6001+", r"A\0000") # FTDI based (Arduino 2009)
		ports += _winList("FTDIBUS", r"FTDIBUS\VID_0403+PID_6001+", r"\0000") # sometimes this works
		ports += _winList("usbser") # ACM based, Arduino Uno, Uno R3, Leonardo
		# usbser should be generic and work for all USB to serial interfaces
		logging.debug("USB serial ports: {}".format(ports))
		return ports
	elif sys.platform == "darwin":
		# /dev/tty.usbserial* for FTDI (0403:6001) in Arduino 2009
		# /dev/tty.usbmodem* for Arduino Uno R3 (2341:0043)
		# the latter probably works for Arduino Leonardo (2341:8036) as well (todo: test)
		with HideStderr():
			s = os.popen('ls -t /dev/tty.usbserial* /dev/tty.usbmodem*').read().rstrip()
		ports = s.split()
		if len(ports)==0:
			logging.info("Could not find USB serial device. Install the FTDI VCP/Arduino driver and plug in the device.")
		if len(ports) > 1:
			logging.debug("Multiple USB serial devices connected, last connected is first in list.")
		logging.debug("USB to serial interfaces: {}".format(ports))
		return ports
	else:
		# /dev/serial/by-id/*FTDI* for FTDI (0403:6001) in Arduino 2009
		# /dev/ttyACM? for Arduino Uno R3 (2341:0043) and Arduino Leonardo (2341:8036)
		# /dev/ttyACM? for Teensy
		try:
			# HideStderr will fail in openSesame since it has no stderr
			with HideStderr():
				s = os.popen('ls -t /dev/serial/by-id/*FTDI* /dev/ttyACM?').read()
		except:
			s = os.popen('ls -t /dev/serial/by-id/*FTDI* /dev/ttyACM?').read()
		ports = s.split()
		if len(ports)==0:
			logging.info("Could not find USB serial device.")
		if len(ports) > 1:
			logging.debug("Multiple USB serial devices connected, last connected is first in list.")
		logging.debug("USB to serial interfaces: {}".format(ports))
		return ports


def getPort(id=0, port=None):
	""" 
	Return serial port.
	id is position in list (0 is latest), port is 'COM1', /dev/tty, 0 or something similar.
	Note that port can also be a real serial port (non USB).
	returns serial connection and id string. 
	"""
	if port != None:
		return port
	else:
		ports = serialList()
		if len(ports)>id:
			port = ports[id]
		else:
			logging.error("id {} invalid, number of USB serial ports found: {}".format(id, len(ports)))
			return None
	if port == None or port == "":
		logging.error("No USB serial port found.")
		return None
	else:
		logging.debug("Connecting to USB serial port: {}".format(port))
	return port

def open(port):
	""" 
	Open serial port.
	port is 'COM1', /dev/tty, 0 or something similar.
	Note that port can also be a real serial port (non USB).
	returns serial connection and id string. In Python 3 this is a string object.
	"""
	
	# port must be str in Python 3, str or unicode in Python 2: convert
	# Python2: converting to unicode is harmless, open() accepts both unicode and str
	# Python3: converting from bytes to unicode is necessary, converting from unicode to unicode will fail
	try:
		port = port.decode("utf-8")
	except:
		pass


	device = None
	while True:
		try:
			device = serial.Serial(port, baudrate=115200, parity='N', timeout = 0.0)  # open serial port
#		except Exception as e:
		except serial.serialutil.SerialException as e:
			if 'Device or resource busy:' in e.__str__():
				logging.debug('Opening COM port is taking a little while, please stand by...')
			else:
				logging.error("Could not connect to serial port {}: \n{}".format(port, e))
				return [None, "Could not connect to serial port"]
		if device is not None:
			break
		time.sleep(1)

		
	# reset connection
	device.flushInput() # race condition, must happen before device sends ID string for devices that do not reset, like Teensy
	# The following three lines cause a reset of the Arduino. 
	# See "Automatic (Software) Reset" in the documentation.
	# Make sure not to send data for the first second after reset.
	device.setDTR(False)
	time.sleep(0.1)
	device.setDTR(True)
	time.sleep(1.0)
	
	#idString = "joystick streaming angle, Ready!" + "0d0a".decode("hex")
	# collect byes up to "!\x0d\x0a" that identify the type of device
	beginTime = time.time()
	bytesRead = b"" # p23
	# read till windows newline for a maximum of 3 seconds
	while len(bytesRead) < 2 or bytesRead[-2:] != b"\x0d\x0a": # p23
		if time.time() > beginTime + TIMEOUT:
			logging.info("USB serial timeout waiting for ID string, got: '{}'".format(bytesRead))
			return (device, "USB serial timeout")
		bytesReading = device.read() # p2: <type 'str'>, p3: <class 'bytes'> (immutable)
		bytesRead += bytesReading
		
	return (device, bytesRead[:-2].decode())


