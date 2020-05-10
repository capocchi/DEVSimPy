# -*- coding: utf-8 -*-

import sys
import os
import string
import zipimport
import importlib
import types
import pkgutil

from traceback import format_exception
from Utilities import listf

def reloadall(module):
	importlib.reload(module)
	for child in pkgutil.walk_packages(module.__path__):
		if isinstance(child, types.ModuleType):
			reloadall(child)

def recompile(modulename):
	"""	recompile module from modulename
	"""

	### modulename is file type
	if os.path.isfile(modulename) and os.path.exists(modulename):
		import ZipManager
		zf = ZipManager.Zip(modulename)
		return zf.Recompile()
	else:

		try:
		### first, see if the module can be imported at all...
			name, ext = os.path.splitext(modulename)
			pkg = '.'.join(modulename.split('.')[0:-1])
			tmp = importlib.import_module(name, package=pkg)
		#tmp = __import__(modulename, globals(), locals(), fromlist = [modulename.split('.')[-1]])

		except Exception as info:
			return info

		### Use the imported module to determine its actual path
		pycfile = os.path.abspath(tmp.__file__)
		modulepath = pycfile.replace('.pyc', '.py') #string.replace(pycfile, ".pyc", ".py")

		### Try to open the specified module as a file
		code = open(modulepath, 'rU').read()

		### see if the file we opened can compile.  If not, return the error that it gives.
		### if compile() fails, the module will not be replaced.
		try:
			compile(code, modulename, "exec")
		except:
			return "Error in compilation: " + str(sys.exc_info()[0]) +"\r\n" + listf(format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
		else:

			### Ok, it compiled.  But will it execute without error?
			try:
				exec(compile(open(modulepath).read(), modulepath, 'exec'), globals())
			except Exception:
				#return "Error '%s' happened on line %d" % (info[0], info[1][1])
				return "Error in execution: " + str(sys.exc_info()[0]) +"\r\n" + listf(format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))

			else:
				### at this point, the code both compiled and ran without error.  Load it up
				### replacing the original code.
				### reload recursivelly!
				try:
					reloadall(tmp)
					return sys.modules[tmp.__name__]
				except:
					sys.stdout.write('Error trying to reload dependencies in recompile module!')
				else:
					return importlib.reload(tmp)