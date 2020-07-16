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

import os
import sys
import zipfile
import zipimport
import io
import re
import inspect
import types
import importlib

import gettext
_ = gettext.gettext

from PluginManager import PluginManager #trigger_event
from traceback import format_exception
from Utilities import listf, path_to_module,install_and_import

#global Cmtp
#Cmtp=0

def get_from_modules(name:str)->types.ModuleType:
	""" get module with the correct name from the name that come from dir().
	"""
	for s,m in sys.modules.items():
		if name in s:
			return m
	return None

def getPythonModelFileName(fn:str)->str:
	""" Get filename of zipped python file.
	"""

	#global Cmtp

	#assert(zipfile.is_zipfile(fn))

	zf = zipfile.ZipFile(fn,'r')

	###	TODO: finally impose : py_file_list = filter(lambda f: f.endswith('.py'))
	### find if python file has same name of model file
	py_file_list = [f for f in zf.namelist() if f.endswith(('.py','.pyc')) and os.path.dirname(f) == '' and f not in ('plugins.py', 'steps.py', 'environment.py', 'strategies.py')]
	zf.close()

	### if there is more than one python file in the zip file
	### we find the correct behavioral file
	if len(py_file_list) > 1:
		model_name = os.path.splitext(os.path.basename(fn))[0]
		for python_file in py_file_list:
			### if the name of python file in zip and the name of the model are similar.
			if os.path.splitext(python_file)[0] == model_name:
				return python_file
			### else test if the python file containing the class inherit of the DomainBehavior or DomainStructure
			else:
				
				import Components
				cls = Components.GetClass(os.path.join(fn, python_file))

				from DomainInterface.DomainBehavior import DomainBehavior
				from DomainInterface.DomainStructure import DomainStructure

				if inspect.isclass(cls):
					if issubclass(cls, DomainBehavior) or issubclass(cls, DomainStructure):
						return python_file

		sys.stdout.write(_('Behavioral python file not found in %s file'%fn))
		raise Exception
	else:
		### zip file must contain python file
		return py_file_list[0]

class Zip:

	def __init__(self, fn:str, files:[str]=[]):
		""" Constructor
		"""
		### local copy
		self.fn = fn

		if files != []:
			self.Create(files)

	def Create(self, add_files:[str]=[])->None:
		dir_name, base_name = os.path.split(self.fn)
		name, ext = os.path.splitext(base_name)

		### output zip file
		zout = zipfile.ZipFile(self.fn, "w")

		### for all files wich could be added
		for fn in [f for f in add_files if os.path.exists(f) or zipfile.is_zipfile(os.path.dirname(f))]:
			fn_dir_name, fn_base_name = os.path.split(fn)
			fn_name, fn_ext = os.path.splitext(fn_base_name)
			### if adding file is compressed, we decompress and add it
			if zipfile.is_zipfile(fn_dir_name):
				zin = zipfile.ZipFile(fn_dir_name, 'r')
				buffer = zin.read(fn_base_name)
				### if not .dat file and the name of file is not the same with the zip file
				#if fn_ext == '.py':
					#zout.writestr("%s%s"%(name,fn_ext), buffer)
				#else:
				zout.writestr(fn_base_name, buffer)
				zin.close()
			else:
				zout.write(fn, fn_base_name)

		zout.close()

	def Update(self, replace_files:[str]=[])->None:
		""" Update zip archive with the new replace file names
		"""

		### delete empty fileName
		replace_files = [f for f in replace_files if f!='']

		# call this function because : http://www.digi.com/wiki/developer/index.php/Error_messages
		Zip.ClearCache(self.fn)

		zin = zipfile.ZipFile(self.fn, 'r')
		zout = zipfile.ZipFile("new_arch.zip", 'w')

		exclude_file = []

		### write all replace file in the new archive
		for fn in replace_files:
			dir_name, base_name = os.path.split(fn)

			if zipfile.is_zipfile(dir_name):
				z = zipfile.ZipFile(dir_name, 'r')
				data = z.read(base_name)
				### if zip file contain image file we can not encode it.
				try:
					zout.writestr(base_name, data)
				except UnicodeDecodeError as info:
					zout.writestr(base_name, data)
				else:
					sys.stdout.write("%s not rewrite\n"%(fn))
					
				z.close()
				
				#sys.stdout.write("update %s from compressed %s\n"%(base_name, fn))
			elif os.path.exists(fn):
				zout.write(fn, base_name)
	
				#sys.stdout.write("update %s from %s\n"%(base_name, fn))
			elif os.path.exists(base_name) and dir_name != "":
				zout.write(base_name, fn)
				
				#sys.stdout.write("update %s from %s\n"%(fn, base_name))
			else:
				exclude_file.append(replace_files.index(fn))
				#sys.stdout.write("%s unknown\n"%(fn))
			
		### try to rewrite not replaced files from original zip
		if not zout.testzip():
			info_list = zin.infolist()
			for item in info_list:
				s = os.path.basename(item.filename)
				if s not in map(os.path.basename, replace_files) and info_list.index(item) not in exclude_file:
					buffer = zin.read(item.filename)
					zout.writestr(item, buffer)
					sys.stdout.write("%s rewrite\n"%(item.filename))
		else:
			sys.stdout.write("%s not updated\n"%(self.fn))

		### close all files
		zout.close()
		zin.close()

		### remove and rename the zip file
		self.ClearFiles()

	def Delete(self, delete_files:[str]=[])->None:
		""" Remove file in zip archive
		"""

		### delete empty fileName
		delete_files = [f for f in delete_files if f!='']

		# call this function because : http://www.digi.com/wiki/developer/index.php/Error_messages
		Zip.ClearCache(self.fn)

		zin = zipfile.ZipFile(self.fn, 'r')
		zout = zipfile.ZipFile("new_arch.zip", 'w')

		###
		info_list = zin.infolist()
		for item in info_list:
			if item.filename not in delete_files:
				buffer = zin.read(item.filename)
				zout.writestr(item, buffer)
				##sys.stdout.write("%s rewrite\n"%(item.filename))

		### close all files
		zout.close()
		zin.close()

		### remove and rename the zip file
		self.ClearFiles()

	def GetImage(self, scaleW:int=16, scaleH:int=16):
		""" Get image object from image file stored in zip file.
			scaleH and scaleW are used to rescale image
		"""

		if zipfile.is_zipfile(self.fn):
			return None

		zf = zipfile.ZipFile(self.fn, 'r')

		### find if python file has same name of model file
		L = [f for f in zf.namelist() if f.endswith(('.jpg','jpeg','png','bmp'))]

		if L != []:
			import wx
			f = zf.open(L.pop())
			buf = f.read()
			f.close()
			zf.close()
			sbuf = io.StringIO(buf)
			image = wx.ImageFromStream(sbuf)
			sbuf.close()
			image.Rescale(scaleW, scaleH)
			return image
		else:
			zf.close()
			return None

	@staticmethod
	def GetPluginFile(fn:str)->str:
		""" TODO: comment
		"""
		### zipfile (amd or cmd)
		zf = zipfile.ZipFile(fn, 'r')
		nl = zf.namelist()
		zf.close()

		L = [a for a in [re.findall("^(plugins[/]?[\w]*.py)$", s) for s in nl] if a!= []]
		return L.pop(0)[0] if L != [] else ""

	@staticmethod
	def HasPlugin(fn:str)->bool:
		""" TODO: comment
		"""

		### zipfile (amd or cmd)
		zf = zipfile.ZipFile(fn, 'r')
		nl = zf.namelist()
		zf.close()

		### plugin file is plugins.pi in root of zipfile or in plugins zipedd directory
		return any([re.search("^(plugins[/]*[\w]*.py)$", s) for s in nl])

	# BDD Test----------------------------------------------------------------------
	@staticmethod
	def HasTests(fn:str)->bool:
		""" TODO: comment
		"""
		module_name = getPythonModelFileName(fn)
		name = os.path.basename(module_name.split('.'))[0]
		zf = zipfile.ZipFile(fn, 'r')
		nl = zf.namelist()
		zf.close()

		return any([re.search("^(BDD/[\w*/]*\.py|BDD/[\w*/]*\.feature)$", s) for s in nl])

	@staticmethod
	def GetTests(fn:str)->[str]:
		""" Return feature, steps and environment files from .amd
		"""
		zf = zipfile.ZipFile(fn, 'r')
		nl = zf.namelist()
		zf.close()

		###
		tests_files = [a for a in [re.findall("^(BDD/[\w*/]*\.py|BDD/[\w*/]*\.feature)$", s) for s in nl] if a!= []]
		tests_files = [a[0] for a in tests_files]

		return tests_files
	# ------------------------------------------------------------------------------

	def GetModule(self, rcp: bool=False)->types.ModuleType:
		""" Return module from zip file corresponding to the amd or cmd model.
			It used when the tree library is created.
			If the module refered by self.fn is already imported, its returned else its imported using zipimport
		"""

		# if necessary, recompile (for update after editing code source of model)
		#if rcp: recompile(module_name)
	
		PluginManager.trigger_event("IMPORT_STRATEGIES", fn=self.fn)
		fullname = "".join([os.path.basename(os.path.dirname(self.fn)), getPythonModelFileName(self.fn).split('.py')[0]])

		return self.ImportModule() if fullname not in sys.modules else sys.modules[fullname]

	def ImportModule(self)->types.ModuleType:
		""" Import module from zip file corresponding to the amd or cmd model.
		"""
		### allows to import the lib from its name (like import MyModel.amd). Dangerous because confuse!
		### Import can be done using: import Name (ex. import MessageCollector - if MessageCollecor is .amd or .cmd)
		p = os.path.dirname(os.path.dirname(self.fn))
		if p not in sys.path:
			sys.path.append(p)

		importer = zipimport.zipimporter(self.fn)
		module_name = getPythonModelFileName(self.fn)

		try:	
			module = importer.load_module(module_name.split('.py')[0])

		### package is needed by the self.module_name (dependency)
		except ModuleNotFoundError as info:
			### get the package name
			package = sys.exc_info()[1].name

			import wx
			dial = wx.MessageDialog(None, _('%s package is needed by %s.\nDo you want to install it?')%(package,module_name), _('Required package'), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
			if dial.ShowModal() == wx.ID_YES:
				### try to install
				if install_and_import(package):
					module = importer.load_module(module_name.split('.py')[0])
				else:
					module = None
			else:
				module = None
				
			dial.Destroy()
		finally:
			if module:
				module.__name__ = path_to_module(module_name)
				
				### allows to import with a reference from the parent directory (like parentName.model).
				### Now import of .amd or .cmd module is composed by DomainModel (no point!).
				### Example : import CollectorMessageCollector
				fullname = "".join([os.path.basename(os.path.dirname(self.fn)), getPythonModelFileName(self.fn).split('.py')[0]]) 
				sys.modules[fullname] = module

				return module
			else:
				return None

	def ReImport(self):
		""" Reimport the module from zip file.
		"""
		Zip.ClearCache(self.fn)

		# import module
#		try:

		### reload submodule from module dependencies!
		fullname = "".join([os.path.basename(os.path.dirname(self.fn)), getPythonModelFileName(self.fn).split('.py')[0]])
		module = sys.modules[fullname]
		domain_name = os.path.basename(os.path.dirname(self.fn))
		for name in dir(module):
			if type(getattr(module, name)) == types.ModuleType:
				### TODO: only reload the local package (not 'sys' and so one)
				importlib.reload(get_from_modules(name))
		
		### clear to clean the import after exporting model (amd or cmd) and reload within the same instance of DEVSimPy
		zipimport._zip_directory_cache.clear()

		### reload module
		module = self.ImportModule()
		return module

#		except Exception as info:
#			msg_i = _("Error in execution: ")
#			msg_o = listf(format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
#			try:
#				sys.stderr.write( msg_i + str(sys.exc_info()[0]) +"\r\n" + msg_o)
#			except UnicodeDecodeError:
#				sys.stderr.write( msg_i + str(sys.exc_info()[0]).decode('latin-1').encode("utf-8") +"\r\n" + msg_o)
#			return info
#		else:
#			return module

	@staticmethod
	def ClearCache(fn:str)->None:
		"""Clear out cached entries from _zip_directory_cache"""

		if fn in zipimport._zip_directory_cache:
			del zipimport._zip_directory_cache[fn]

		if fn not in sys.path:
			sys.path.append(fn)

	def ClearFiles(self)->None:
		""" remove and rename the zip file.
		"""
		try:
			os.remove(self.fn)
		except Exception as info:
			#sys.exc_info()
			sys.stderr.write(_('File has not been deleted: %s'%info))

		try:
			os.rename("new_arch.zip", self.fn)
		### os.rename dont work in Linux OS with linked file (copy/paste for exemple)
		except OSError:
			import shutil
			if os.path.exists(self.fn):
				try:
					shutil.move("new_arch.zip", self.fn)
				except:
					pass
