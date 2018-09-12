#!/usr/bin/python
import os
from setuptools import setup

def read(fname):
	"""
	Utility function to read the README file.
	Used for the long_description.  It's nice, because now 1) we have a top level
	README file and 2) it's easier to type in the README file than to put a raw
	string in below ...
	"""
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
	name = "RuSocSci",
	version = "0.8.5",
	install_requires = "pyserial",
	python_requires = ">=2.6",
	author = "Wilbert van Ham",
	author_email = "w.vanham@socsci.ru.nl",
	description = "Support package for Radboud University Nijmegen, "\
			"Faculty of Social Sciences hardware, with PsychoPy-like API.",
	license = "GPLv3+",
	keywords = "hardware",
	url = "https://www.socsci.ru.nl/wilberth/python/rusocsci.html",
	packages = ['rusocsci'],
	long_description = read('README'),
	classifiers=[
		"Development Status :: 4 - Beta",
		"License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
	],
)
print("post install")
	
