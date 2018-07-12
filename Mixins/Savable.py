# -*- coding: utf-8 -*-

"""
Name: Savable.py
Brief descritpion:
Author(s): L. Capocchi <capocchi@univ-corse.fr>, A-T. Luciani <atluciani@univ-corse.fr>
Version:  1.0
Last modified: 2012.04.04
GENERAL NOTES AND REMARKS:

GLOBAL VARIABLES AND FUNCTIONS:
"""

import os
import sys
import cPickle
import zipfile
import zipimport
import gzip
import re
import inspect
import __builtin__
import gettext
#import wx

_ = gettext.gettext

try:
	import yaml
	__builtin__.__dict__['YAML_IMPORT'] = True
except ImportError, info:
	__builtin__.__dict__['YAML_IMPORT'] = False
	sys.stdout.write("yaml module was not found! Install it if you want to save model in yaml format.\n")

from tempfile import gettempdir

from Decorators import BuzyCursorNotification, StatusBarNotification, cond_decorator
from Utilities import itersubclasses, getTopLevelWindow
from XMLModule import makeDEVSXML, getDiagramFromXMLSES
from Join import makeJoin, makeDEVSConf
from Abstractable import Abstractable

import Components
import ZipManager

class PickledCollection(list):
	""" Custom list class for dsp attributes dumping
	"""

	def __init__(self, obj):
		""" Constructor
		"""
		self.obj = obj
		self.pickled_obj = [getattr(self.obj, attr) for attr in self.obj.dump_attributes]

		#=======================================================================
		### addition of abstraction attributes only if there is not in dump_attributes (after having saved a model, dump_attributes contains abstraction attributes !)
		self.pickled_obj += [getattr(self.obj, attr) for attr in self.obj.dump_abstr_attributes if attr not in self.obj.dump_attributes]
		#=======================================================================

	def __setstate__(self, state):
		""" Restore state from the unpickled state values.
		"""
		self.__dict__.update(state)

	def __iter__(self):
		""" Overwrite iterator protocol
		"""
		for v in self.pickled_obj:
			yield v

class DumpBase(object):
	""" DumpBase class
	"""

	### list of available extension
	WhiteList = ('.cmd','.amd', '.dsp', '.js', '.xml', '.yaml', '.yml', '.tar','.zip','.rar','.7zip','.tar','.gz','.7z','.s7z','.ace','.afa','.alz','.apk','.arc','.arj','.ba','.bh','.cab','.cfs','.cpt','.dra','.dd','.dgc','.dmg','.gca','.ha','hki.','.ice','.j','.kgb','.lzh','.lha','.lzx','.pak','.partimg','.paq6','.paq7','.paq8','.pea','.pim','.pit','.qda','.rk','.sda','.sea','.sen','.sfx','.sit','.sitx','.sqx','.tgz','.Z','.bz2','.tbz2','.lzma','.tlz','.uc','.uc0','.uc2','.ucn','.ur2','.ue2','.uca','.uha','.wim','.xar','.xp3','.yz1','.zipx','.zoo','.zz','.rz','.sfark')

	### Dict of tuples extension/class
	DB = {}

	### extension is in whiteList
	@staticmethod
	def GetExt(fileName=""):
		ext = os.path.splitext(fileName)[-1]
		if ext in DumpBase.WhiteList:
			return ext
		else:
			sys.stdout.write(_("\nThis extension is unknown: %s")%ext)
			return False

	### Return the class in charge of saving or loading from ext of object.
	@staticmethod
	def GetAssociateCls(ext=""):
		try:
			return DumpBase.DB[ext]
		except KeyError:
			return False

	### R�cup�re les fils de la classe pass� en param�tre, ici on veut que ce soit DumpBase, on les ajoute a une liste (subclasses),
	### ensuite pour chaque element de la liste on recupere la variable static ext (list),
	### et on ajoute au dictionnaire DumpBase.vars en cl� l'extension ext et en valeur le nom de la classe correspondante
	@staticmethod
	def PopulateDB():
		"""
		"""

		subclasses = itersubclasses(DumpBase)

		for cls in subclasses:
			for elem in cls.ext:
				# Impose un type de fichier par classe et non pas une classe par type de fichier.
				assert(elem not in DumpBase.DB.keys())
				DumpBase.DB[elem] = cls

	def Load(self, filename):
		"""Retrieve data from the file source."""
		pass

	def Save(self, filename):
		"""Save the data object to the file."""
		pass

###-----------------------------------------------------------
class DumpZipFile(DumpBase):
	""" For save .amd or cmd file
	"""

	ext = [".amd", ".cmd"]

	def Save(self, obj_dumped, fileName = None):
		""" Function that save the codeblock on the disk.
		"""
		assert(fileName.endswith(tuple(DumpZipFile.ext)))

		### local copy of paths
		python_path = obj_dumped.python_path
		image_path = obj_dumped.image_path

		### Now, file paths are in the compressed file
		if os.path.isabs(python_path):
			obj_dumped.python_path = os.path.join(fileName, os.path.basename(obj_dumped.python_path))

		if os.path.isabs(image_path):
			obj_dumped.image_path = os.path.join(fileName, os.path.basename(obj_dumped.image_path))

		obj_dumped.model_path = fileName

		### args is constructor args and we save these and not the current value
		if hasattr(obj_dumped, 'args'):
			obj_dumped.args = Components.GetArgs(Components.GetClass(obj_dumped.python_path))

		try:

			fn = 'DEVSimPyModel.dat'

			### dump attributes in fn file
			cPickle.dump(	obj = PickledCollection(obj_dumped),
							file = open(fn, "wb"),
							protocol = 0)

		except Exception, info:

			sys.stderr.write(_("Problem saving (during the dump): %s -- %s\n")%(str(fileName),info))
			return False
		else:

			try:

				zf = ZipManager.Zip(fileName)

				### create or update fileName
				if os.path.exists(fileName):

					zf.Update(replace_files = [fn, python_path, image_path])
				else:
					zf.Create(add_files = [fn, python_path, image_path])

				os.remove(fn)

				## abs path of the directory that contains the file to export (str() to avoid unicode)
				newExportPath = str(os.path.dirname(fileName))

				mainW = getTopLevelWindow()
				### if export on local directory, we insert the path in the config file
				if not os.path.basename(DOMAIN_PATH) in newExportPath.split(os.sep):
					### update of .devsimpy config file
					mainW.exportPathsList = eval(mainW.cfg.Read("exportPathsList"))
					if newExportPath not in mainW.exportPathsList:
						mainW.exportPathsList.append(str(newExportPath))
					mainW.cfg.Write("exportPathsList", str(eval("mainW.exportPathsList")))

				### if lib is already in the lib tree, we update the tree
				mainW.tree.UpdateDomain(newExportPath)
				### to sort lib tree
				mainW.tree.SortChildren(mainW.tree.root)

			except Exception, info:

				sys.stderr.write(_("Problem saving (during the zip handling): %s -- %s\n")%(str(fileName),info))
				return False
			else:

				return True

	def Load(self, obj_loaded, fileName = None):
		""" Load codeblock (obj_loaded) from fileName
		"""

		# get zip file object
		zf = zipfile.ZipFile(fileName, 'r')

		try:
			data_file = 'DEVSimPyModel.dat'
			path = zf.extract(data_file, gettempdir())
		except KeyError, info:
			sys.stderr.write(_("ERROR: Did not %s find in zip file %s --\n%s \n")%(data_file, str(fileName), info))
			return info
		except Exception, info:
			sys.stderr.write(_("Problem extracting: %s -- %s \n")%(str(fileName),info))
			return info
		finally:
			zf.close()

		### cPickle need importation (mostly when the instanciation is extrernal of DEVSimPy library)
		#module = BlockFactory.GetModule(fileName)

		#if isinstance(module, Exception):
			#return module

		# try to load file
		try:
			f = open(path,'rb')
			L = cPickle.load(f)
			f.close()
		except Exception, info:
			sys.stderr.write(_("Problem loading: %s -- %s \n")%(str(fileName), info))
			return info
	
		### Check comparison between serialized attribut (L) and normal attribut (dump_attributes)
		### for model build with a version of devsimpy <= 2.5
		### font checking
		#if wx.VERSION_STRING >= '4.0': wx.FONTFAMILY_SWISS = wx.SWISS
		if len(obj_loaded.dump_attributes) != len(L):
			if fileName.endswith(DumpZipFile.ext[-1]):
				if not isinstance(L[9], list):
					import wx
					L.insert(9, [FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, u'Arial'])
			else:
				if not isinstance(L[6], list):
					import wx
					L.insert(6, [FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, u'Arial'])


		### label_pos checking
		if len(obj_loaded.dump_attributes) != len(L):

			### 'label_pos' attribut is on rank 6 and its defautl value is "middle"
			j = 6 if fileName.endswith(DumpZipFile.ext[-1]) else 4
			L.insert(j, 'middle')

		#=======================================================================

		### abstraction hierarchy checking
		if abs(len(obj_loaded.dump_attributes)-len(L)) == len(Abstractable.DUMP_ATTR):
			obj_loaded.dump_attributes += Abstractable.DUMP_ATTR

		#=======================================================================
		assert(len(L)==len(obj_loaded.dump_attributes))

		try:
			### assign dumped attributs
			for i, attr in enumerate(obj_loaded.dump_attributes):
				### update behavioral attribute for model saved with bad args (amd or cmd have been changed in librairie but not in dsp)
				if attr == 'args':
					if obj_loaded.args != {}:
						for key in filter(L[i].has_key, obj_loaded.args.keys()):
							obj_loaded.args[key] = L[i][key]
					else:
						setattr(obj_loaded, attr, L[i])
				else:
					setattr(obj_loaded, attr, L[i])
				

		except IndexError, info:
			sys.stderr.write(_("Problem loading (old model): %s -- %s \n")%(str(fileName), info))
			return info

		
		### if the model was made from another pc
		if not os.path.exists(obj_loaded.model_path):
			obj_loaded.model_path = fileName

		### if python file is wrong
		if not os.path.exists(os.path.dirname(obj_loaded.python_path)):
			### ?: for exclude or non-capturing rule
			obj_loaded.python_path = os.path.join(obj_loaded.model_path, re.findall(".*(?:.[a|c]md)+[/|\\\](.*.py)*", obj_loaded.python_path)[-1])

		return True

	@BuzyCursorNotification
	def LoadPlugins(self, obj, fileName):
		""" Method which load plugins from zip
			Used for define or redefine method of amd. and .cmd model
			The name of plugin file must be "plugins.py"
		"""
		### if list of activated plugins is not empty
		if obj.plugins != []:
			### import zipfile model
			if zipfile.is_zipfile(fileName):
				importer = zipimport.zipimporter(fileName)
				if importer.find_module('plugins'):

					try:
						module = importer.load_module('plugins')
					except ImportError, info:
						sys.stdout.write("%s\n"%info)
						return info

					for m in [e for e in map(module.__dict__.get, dir(module)) if not inspect.ismodule(e) and inspect.getmodule(e) is module]:
						name = m.__name__
						### import only plugins in plugins list (dynamic attribute)
						if name in obj.plugins:
							try:
								### new object to assaign
								new = eval("module.%s"%name)
								if inspect.isfunction(new):
									setattr(obj, name, types.MethodType(new, obj))
								elif inspect.isclass(new):
									### TODO: monkey patchin !!! (most simple is to change python file for override class)
									pass

							except Exception, info:
								sys.stdout.write(_('plugins %s not loaded : %s\n'%(name,info)))
								return info

		### restor method which was assigned to None before being pickled
		else:
			### for all method in the class of model
			for method in filter(lambda value: isinstance(value, types.FunctionType), obj.__class__.__dict__.values()):
				name = method.__name__
				### if method was assigned to None by getstate berfore being pickled
				if getattr(obj, name) is None:
					### assign to default class method
					setattr(obj, name, types.MethodType(method, obj))

		return True

###-----------------------------------------------------------
class DumpGZipFile(DumpBase):
	""" For save .dsp file
	"""
	ext = [".dsp"]

	def Save(self, obj_dumped, fileName = None):
		""" Function that save the dump on the disk under filename.
		"""

		assert(fileName.endswith(tuple(DumpGZipFile.ext)))

		try:
			cPickle.dump(   obj = PickledCollection(obj_dumped),
							file = gzip.GzipFile(filename = fileName, mode = 'wb', compresslevel = 9),
							protocol = 0)

		except Exception, info:
			sys.stderr.write(_("\nProblem saving: %s -- %s\n")%(str(fileName),info))
			return False
		else:
			return True

	def Load(self, obj_loaded, fileName = None):
		""" Function that save the dump on the disk with the filename.
		"""

		# try to open f with compressed mode
		try:
			f = gzip.GzipFile(filename = fileName, mode='rb')
			f.read(1) # trigger an exception if is not compressed
			f.seek(0)

		except Exception, info:
			sys.stderr.write(_("Problem opening: %s -- %s\n")%(str(fileName), info))
			return info

		else:
			### try to load serialized file
			try:
				dsp = cPickle.load(f)
			except Exception, info:
				sys.stderr.write(_("Problem loading: %s -- %s\n")%(str(fileName), info))
				return info
			finally:
				f.close()

			#=======================================================================

			if abs(len(obj_loaded.dump_attributes)-len(dsp)) == len(Abstractable.DUMP_ATTR):
				obj_loaded.dump_attributes += Abstractable.DUMP_ATTR

			#=======================================================================

			a,b = map(len, (obj_loaded.dump_attributes, dsp))
			assert(a==b)

			### assisgn the specific attributs
			for i,attr in enumerate(obj_loaded.dump_attributes):
				setattr(obj_loaded, attr, dsp[i])

			obj_loaded.last_name_saved = fileName

			return True

###-----------------------------------------------------------
class DumpYAMLFile(DumpBase):
	""" For save .yaml file
	"""
	ext = [".yaml", '.yml']

	def Save(self, obj_dumped, fileName = None):
		""" Function that save the dump on the disk under filename.
		"""

		assert(fileName.endswith(tuple(DumpYAMLFile.ext)))

		try:

			f = open(fileName, 'w')
			yaml.dump(PickledCollection(obj_dumped), f)
			f.close()

		except Exception, info:
			sys.stderr.write(_("\nProblem saving: %s -- %s\n")%(str(fileName),info))
			return False
		else:
			return True

	def Load(self, obj_loaded, fileName = None):
		""" Function that save the dump on the disk with the filename.
		"""

		## try to open f with compressed mode
		try:

			f = open(fileName, 'r')
			dsp = yaml.load(f)
			f.close()

		except Exception, info:
			sys.stderr.write(_("Problem opening: %s -- %s\n")%(str(fileName), info))
			return info

		else:

			### assisgn the specific attributs
			for i,attr in enumerate(obj_loaded.dump_attributes):
				setattr(obj_loaded, attr, dsp[i])

			obj_loaded.last_name_saved = fileName

			return True

###-----------------------------------------------------------
class DumpJSFile(DumpBase):
	""" For save .js file
	"""
	ext = [".js"]

	def Save(self, obj_dumped, fileName = None):

		assert(fileName.endswith(tuple(DumpJSFile.ext)))

		diagram = obj_dumped

		addInner = []
		liaison = []
		model = {}
		labelEnCours = str(diagram.label)
		#Position initial du 1er modele
		x = [40]
		y = [40]
		bool = True
		model, liaison, addInner = makeJoin(diagram, addInner, liaison, model, bool, x, y, labelEnCours)
		makeDEVSConf(model, liaison, addInner, fileName)

###-----------------------------------------------------------
class DumpXMLFile(DumpBase):
	""" For save .xml file
	"""
	ext = [".xml"]

	def Save(self, obj_dumped, fileName = None):

		assert(fileName.endswith(tuple(DumpXMLFile.ext)))

		diagram = obj_dumped
		D = diagram.__class__.makeDEVSGraph(diagram, {})

		if isinstance(diagram, Components.GenericComponent):
			label = diagram.label
		else:
			label = os.path.splitext(os.path.basename(fileName))[0]

		makeDEVSXML(label, D, fileName)

		return True

###-----------------------------------------------------------
class Savable(object):
	""" Savable class that allows methods to save and load diagram into file.

		cond_decorator is used to enable/diseable the cursor notification depending on the GUI/NO_GUI use of DEVsimPy.
	"""

	### static attribut to store le extention/class available
	DB  = DumpBase.PopulateDB()

	@cond_decorator(__builtin__.__dict__['GUI_FLAG'], BuzyCursorNotification)
	@cond_decorator(__builtin__.__dict__['GUI_FLAG'], StatusBarNotification('Sav'))
	def SaveFile(self, fileName = None):
		""" Save object in fileName
		"""
		if fileName is None:
			return False

		### test if ext is acceptable
		ext = DumpBase.GetExt(fileName)
		if ext:
			### get class managing object with this extension
			cls = DumpBase.GetAssociateCls(ext)
			if cls:
				### call Save method of self to save it in fileName file.
				return cls().Save(self, fileName)
			else:
				sys.stdout.write(_("\nError in Savable class using SaveFile: %s")%fileName)
				return False
		else:
			sys.stdout.write(_("\nUnknown extension: %s")%fileName)
			return False

	@cond_decorator(__builtin__.__dict__['GUI_FLAG'], StatusBarNotification('Load'))
	def LoadFile(self, fileName = None):
		""" Load object from fileName
		"""

		if fileName is None:
			return False

		### test if ext is acceptable
		ext = DumpBase.GetExt(fileName)
		if ext:
			### get class managing object with this extension
			cls = DumpBase.GetAssociateCls(ext)
			if cls:
				### call Load method of self to load it from fileName file.
				return cls().Load(self, fileName)
			else:
				sys.stdout.write(_("Error in Savable class using LoadFile: %s")%fileName)
				return False
		else:
			sys.stdout.write(_("Unknown extension: %s")%fileName)
			return False