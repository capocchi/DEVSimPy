# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Plugable.py ---
#                     --------------------------------
#                        Copyright (c) 2013
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 19/11/13
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##-

import sys
import os
import zipimport
import imp
import inspect
import types
import zipfile

import Decorators

#---------------------------------------------------------
class Plugable:
	""" Plugable Mixin
	"""

	@staticmethod
	def Load_Module(fileName):
		""" Load module without load_module from importer. \
		In this way, we can change the name of module in the built-in.
		"""

		### import zipfile model
		if zipfile.is_zipfile(fileName):
			importer = zipimport.zipimporter(fileName)

			### change module name
			old_plugin_name = 'plugins'
			new_plugin_name = '%s.%s'%(os.path.basename(os.path.splitext(fileName)[0]), old_plugin_name)

			### get code of plug-ins
			code =  importer.get_code(old_plugin_name)

			# Create the new 'temp' module.
			temp = imp.new_module(new_plugin_name)
			sys.modules[new_plugin_name] = temp

			### there is syntax error ?
			try:
				exec code in temp.__dict__
			except Exception, info:
				return info

			return sys.modules[new_plugin_name]

		return None

	@Decorators.BuzyCursorNotification
	def LoadPlugins(self, fileName):
		""" Method which load plug-ins from zip
			Used for define or redefine method of amd. and .cmd model
			The name of plug-in file must be "plugins.py"
		"""

		if hasattr(self,'plugins'):
			### if list of activated plug-ins is not empty
			if self.plugins != []:
				module = Plugable.Load_Module(fileName)

				if inspect.ismodule(module):

					for name,m in inspect.getmembers(module, inspect.isfunction):
						### import only plug-ins in plug-ins list (dynamic attribute) and only method
						if name in self.plugins and 'self' in inspect.getargspec(m).args:
							setattr(self, name, types.MethodType(m, self, self.__class__))
				else:
					return module
			### restore method which was assigned to None before being pickled
			else:
				### for all method in the class of model
				for method in filter(lambda value: isinstance(value, types.FunctionType), self.__class__.__dict__.values()):
					name = method.__name__
					### if method was assigned to None by getstate before being pickled
					if getattr(self, name) is None:
						### assign to default class method
						setattr(self, name, types.MethodType(method, self))

		return True

def main():
    pass

if __name__ == '__main__':
    main()
