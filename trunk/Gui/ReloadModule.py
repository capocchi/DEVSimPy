# -*- coding: utf-8 -*-
import sys
import string
from traceback import format_exception

def listf(data):
	buffer = ""
	for line in data:
		buffer = buffer + line + "\n"
	return buffer

def recompile(modulename):
	"""	recompile module from modulename
	"""
	
	### first, see if the module can be imported at all...
	try:
		tmp = __import__(modulename)
	except:
		return "Couldn't import module %s"%(modulename)

	### Use the imported module to determine its actual path
	pycfile = tmp.__file__
	modulepath = string.replace(pycfile, ".pyc", ".py")


	### Try to open the specified module as a file
	try:
		code=open(modulepath, 'rU').read()
	except:
		return "Error opening file: %s Does it exist?"%(modulepath)

	
	### see if the file we opened can compile.  If not, return the error that it gives.
	### if compile() fails, the module will not be replaced.
	try:
		compile(code, modulename, "exec")
	except:
		return "Error in compilation: " + str(sys.exc_info()[0]) +"\r\n" + listf(format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
	else:
		
		### Ok, it compiled.  But will it execute without error?	
		try:
			execfile(modulepath)
		except Exception, info:
			return "Error '%s' happened on line %d" % (info[0], info[1][1])
			#return "Error in execution: " + str(sys.exc_info()[0]) +"\r\n" + listf(format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))

		else:
			
			### at this point, the code both compiled and ran without error.  Load it up
			### replacing the original code.
			reload(sys.modules[modulename])
		
		return "Module %s reloaded"%(modulename)