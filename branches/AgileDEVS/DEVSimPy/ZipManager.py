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
import StringIO
import re
import wx
import inspect

from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.DomainStructure import DomainStructure

from traceback import format_exception
from Utilities import listf, path_to_module

#global Cmtp
#Cmtp=0

def getPythonModelFileName(fn):
	""" Get filename of zipped python file 
	"""
	
	#global Cmtp
	
	assert(zipfile.is_zipfile(fn))
	
	zf = zipfile.ZipFile(fn,'r')
	
	###	TODO: finally impose : py_file_list = filter(lambda f: f.endswith('.py'))
	### find if python file has same name of model file
	py_file_list = filter(lambda f: f.endswith('.py') and os.path.dirname(f) == '' and f not in ('plugins.py', 'steps.py', 'environment.py'), zf.namelist())
	zf.close()

	#Cmtp+=1
	#print Cmtp, fn

	### if there is more than one python file in the zip file
	### we find the correct behavioral file
	if len(py_file_list) > 1:
		model_name = os.path.splitext(os.path.basename(fn))[0]
		for python_file in py_file_list:
			### if the name of python fiel in zip and the name of the model are similar.
			if os.path.splitext(python_file)[0] == model_name:
				return python_file
			### esle test if the python file containing the class inherit of the DomainBehavior or DomainStructure
			else:
				import Components
				cls = Components.GetClass(os.path.join(fn, python_file))
				
				if inspect.isclass(cls):
					if issubclass(cls, DomainBehavior) or issubclass(cls, DomainStructure):
						return python_file
						
		sys.stdout.write(_('Behavioral python file not found in %s file'%fn))
		raise Exception
	else:
		### zip file must contain python file
		return py_file_list[0]

class Zip:
	
	def __init__(self, fn, files = []):
		""" Constructor
		"""
		### local copy
		self.fn = fn
		
		if files != []:
			self.Create(files)
		
	def Create(self, add_files = []):
		dir_name, base_name = os.path.split(self.fn)
		name, ext = os.path.splitext(base_name)
		
		### output zip file
		zout = zipfile.ZipFile(self.fn, "w")
		
		### for all files wich could be added
		for fn in filter(lambda f: os.path.exists(f) or zipfile.is_zipfile(os.path.dirname(f)), add_files):
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

	def Update(self, replace_files=[]):
		""" Update zip archive with the new replace file names
		"""

		### delete empty fileName
		replace_files = filter(lambda f: f!='', replace_files)
		
		# call this function because : http://www.digi.com/wiki/developer/index.php/Error_messages
		self.ClearCache()

		zin = zipfile.ZipFile(self.fn, 'r')
		zout = zipfile.ZipFile("new_arch.zip", 'w')

		exclude_file = []
		
		### write all replace file in the new archive
		for fn in replace_files:
			dir_name, base_name = os.path.split(fn)
			
			if zipfile.is_zipfile(dir_name):
				#print '1'
				z = zipfile.ZipFile(dir_name, 'r')
				data = z.read(base_name)
				### this line is in comment because is zip file contain image file we can not encode it.
				zout.writestr(base_name, data.encode('utf-8'))
				#zout.writestr(base_name, data)
				z.close()
				#print '11'
				#sys.stdout.write("update %s from compressed %s\n"%(base_name, fn))
			elif os.path.exists(fn):
				#print '2'
				zout.write(fn, base_name)
				#print '22'
				#sys.stdout.write("update %s from %s\n"%(base_name, fn))
			elif os.path.exists(base_name) and dir_name != "":
				#print '3'
				zout.write(base_name, fn)
				#print '33'
				#sys.stdout.write("update %s from %s\n"%(fn, base_name))
			else:
				exclude_file.append(replace_files.index(fn))
				#sys.stdout.write("%s unknown\n"%(fn))
		
		### try to rewrite not replaced files from original zip
		info_list = zin.infolist()
		for item in info_list:
			s = os.path.basename(item.filename)
			if s not in map(os.path.basename, replace_files) and info_list.index(item) not in exclude_file:
				buffer = zin.read(item.filename)
				zout.writestr(item, buffer)
				sys.stdout.write("%s rewrite\n"%(item.filename))

		### close all files
		zout.close()
		zin.close()

		### remove and rename the zip file
		self.ClearFiles()
			
	def Delete(self, delete_files=[]):
		""" Remove file in zip archive
		"""

		### delete empty fileName
		delete_files = filter(lambda f: f!='', delete_files)

		# call this function because : http://www.digi.com/wiki/developer/index.php/Error_messages
		self.ClearCache()

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
			
	def GetImage(self, scaleW=16, scaleH=16):
		""" Get image object from image file stored in zip file.
			scaleH and scaleW are used to rescale image
		"""
	
		zf = zipfile.ZipFile(self.fn, 'r')
		
		### find if python file has same name of model file
		L = filter(lambda f: f.endswith(('.jpg','jpeg','png','bmp')), zf.namelist())
		
		if L != []:
			f=zf.open(L.pop())
			buf = f.read()
			f.close()
			sbuf = StringIO.StringIO(buf)
			image = wx.ImageFromStream(sbuf)
			image.Rescale(scaleW, scaleH)
			zf.close()
			return image
		else:
			return None
	
	@staticmethod
	def GetPluginFile(fn):
		""" TODO: comment
		"""
		### zipfile (amd or cmd)
		zf = zipfile.ZipFile(fn, 'r')
		nl = zf.namelist()
		zf.close()
		
		L = filter(lambda a: a!= [],map(lambda s: re.findall("^(plugins[/]?[\w]*.py)$", s), nl))
		return L.pop(0)[0] if L != [] else ""
		
	@staticmethod
	def HasPlugin(fn):
		""" TODO: comment
		"""
		
		### zipfile (amd or cmd)
		zf = zipfile.ZipFile(fn, 'r')
		nl = zf.namelist()
		zf.close()
		### plugin file is plugins.pi in root of zipfile or in plugins zipedd directory
		return any(map(lambda s: re.search("^(plugins[/]*[\w]*.py)$", s), nl))
	
	# BDD Test----------------------------------------------------------------------
	@staticmethod
	def HasTests(fn):
		""" TODO: comment
		"""
		name = os.path.basename(getPythonModelFileName(fn)).split('.')[0]
		zf = zipfile.ZipFile(fn, 'r')
		nl = zf.namelist()
		zf.close()
		return any(map(lambda s: re.search("^(BDD/[\w*/]*\.py|BDD/[\w*/]*\.spec)$", s), nl))

	@staticmethod
	def GetTests(fn):
		""" Return feature, steps and environment files from .amd
		"""
		zf = zipfile.ZipFile(fn, 'r')
		nl = zf.namelist()

		zf.close()

		###
		tests_files = filter(lambda a: a!= [], map(lambda s:re.findall("^(BDD/[\w*/]*\.py|BDD/[\w*/]*\.spec)$", s), nl))
		tests_files = [a[0] for a in tests_files]

		return tests_files
	# ------------------------------------------------------------------------------
	
	def GetModule(self, rcp=False):
		""" Load module from zip file corresponding to the amd or cmd model.
			It used when the tree library is created.
		"""
		
		# get module name
		try:
			module_name = getPythonModelFileName(self.fn)
		except Exception, info:
			sys.stderr.write(_("Error in ZipManager class for GetModule: no python file in the archive\n"))
			return info

		# if necessary, recompile (for update after editing code source of model)
		#if rcp: recompile(module_name)

		# import module
		try:
			### clear to clean the import after exporting model (amd or cmd) and reload within the same instrance of DEVSimPy
			zipimport._zip_directory_cache.clear()
		
			importer = zipimport.zipimporter(self.fn)
			module = importer.load_module(module_name.split('.py')[0])
			module.__name__ = path_to_module(module_name)
		except Exception, info:
			sys.stderr.write(_("Error in execution: ") + str(sys.exc_info()[0]) +"\r\n" + listf(format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)))
			return info
			
		else:
			return module
	
	def Recompile(self):
		""" recompile module from zip file
		"""
		self.ClearCache()
		return self.GetModule()
		
	def ClearCache(self):
		"""Clear out cached entries from _zip_directory_cache"""

		if self.fn in zipimport._zip_directory_cache:
			del zipimport._zip_directory_cache[self.fn]

		if self.fn not in sys.path:
			sys.path.append(self.fn)
			
	def ClearFiles(self):
		""" remove and rename the zip file
		"""
		
		os.remove(self.fn)
		try:
			os.rename("new_arch.zip", self.fn)	
		### os.rename dont work in Linux OS with linked file (copy/paste for exemple)
		except OSError:
			import shutil	
			shutil.move("new_arch.zip", self.fn)
	