# -*- coding: utf-8 -*-

"""
Name: ZipManager.py
Brief descritpion: Static class dedicated to the zip file managment
Author(s): L. Capocchi <capocchi@univ-corse.fr>
Version:  1.0
Last modified: 2012.12.16
GENERAL NOTES AND REMARKS:

GLOBAL VARIABLES AND FUNCTIONS:
"""

import sys
import imp
import httplib
from urlparse import urlparse

class Net:
	
	def __init__(self, py_net_file):
		"""
		"""
		
		assert(py_net_file.startswith('http'))
		
		self._py_net_file = py_net_file
		
	
	def GetMoldule(python_file=""):
		""" Give module object from url.
		"""

		# See if the module has already been imported
		module_name = self._py_net_file.split('/')[-1].split('.py')[0]

		try:
			return sys.modules[module_name]
		except KeyError:
			pass

		### make new module
		mod = imp.new_module(module_name)
		sys.modules[module_name] = mod
		mod.__file__ = self._py_net_file

		### parse url to extract the path(/devsimpy/domain...) and the network location (lcapocchi.free.fr)
		o = urlparse(self._py_net_file)

		### open conenction
		c = httplib.HTTPConnection(o.netloc)
		### request with GET mode

		c.request('GET', o.path)
		### get response of request
		r = c.getresponse()
		### convert file into string
		code = r.read()
		
		### try to execute module code
		if r.status == 200:
			try:
				exec code in mod.__dict__
				return mod
			except Exception, info:
				return info
		else:
			return r.status
