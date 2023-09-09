# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Components.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 03/15/20
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import builtins

import os
import sys
import zipfile
import re
import types
import importlib
import subprocess
import tempfile

import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec
    
import gettext
_ = gettext.gettext

from tempfile import gettempdir

if builtins.__dict__.get('GUI_FLAG',True):
	import wx
	from pubsub import pub as Publisher
	import Editor
	from SimpleFrameEditor import FrameEditor

import ZipManager

from Utilities import replaceAll, GetActiveWindow, printOnStatusBar, install
from Decorators import BuzyCursorNotification
from NetManager import Net
from shutil import which

###########################################################
###
### 		GENERAL FUNCTIONS
###
###########################################################

def getClassMember(python_file = ''):
	""" Get class member from python file.
	"""
	module  = BlockFactory.GetModule(python_file)
	
	if inspect.ismodule(module):
		## classes composing the imported module
		return dict(inspect.getmembers(module, inspect.isclass))
		
	### exception in module
	return module

def GetClass(elem):
	""" Get python class from filename.
	"""

	clsmembers = getClassMember(elem)
 
	if isinstance(clsmembers, dict):
	
		from DomainInterface.DomainBehavior import DomainBehavior
		from DomainInterface.DomainStructure import DomainStructure

		# moduleName = path_to_module(elem)

		# if 'DomainBehavior' in clsmembers:
			# DomainClass = clsmembers['DomainBehavior']
		# elif 'DomainStructure' in clsmembers:
			# DomainClass = clsmembers['DomainStructure']
		# elif 'Port' in clsmembers:
			# DomainClass = clsmembers['Port']
		# else:
			# DomainClass = clsmembers[os.path.basename(elem).split('.')[0]]
			# sys.stderr.write(_("Class unknown..."))
			# return None

		### return only the class that inherite of DomainBehavoir or DomainStructure which are present in the clsmembers dict
		# return next(filter(lambda c: c != DomainClass and issubclass(c, DomainClass), clsmembers.values()), None)

		DomainClass = (DomainBehavior,DomainStructure,)
		if 'Port' in clsmembers:
			DomainClass += (clsmembers['Port'],)
  
		cls = next(filter(lambda c: c not in DomainClass and issubclass(c, DomainClass) and c.__name__ in elem, clsmembers.values()), None)

		if not cls: sys.stderr.write(_("Class unknown..."))

		return cls

		#for cls in [c for c in clsmembers.values() if c != DomainClass]:
		#	if issubclass(cls, DomainClass):
			#if str(cls.__module__) in str(moduleName):
		#		return cls
	else:
		return clsmembers

def GetArgs(cls = None):
	""" Get behavioral attribute from python file through constructor class.
	"""

	if inspect.isclass(cls):
		try:
			constructor = inspect.getargspec(cls.__init__)
			return dict(list(zip(constructor[0][1:], constructor[3]))) if constructor[3] != None else {}
		except ValueError:
			constructor = inspect.signature(cls.__init__)
			parameters = constructor.parameters
			parameter_dict = {}

			for name, parameter in parameters.items():
				if name != 'self':
					if parameter.default != inspect.Parameter.empty:
						parameter_dict[name] = parameter.default

			return parameter_dict

	#sys.stderr.write(_("Error in GetArgs: First parameter is not a class\n"))
	return None

###########################################################
###
### 		GENERAL CLASSES
###
###########################################################

class DSPComponent:
	"""
	"""
	@staticmethod
	def Load(filename, label, canvas):
		""" Load component from filename.
		"""
		from Container import Diagram
		#assert(filename.endswith('.dsp'))

		# its possible to use the orignal copy of the droped diagram
		dial = wx.MessageDialog(canvas, _('Do you want to open the orignal diagram in a new tab?'), label, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

		new_tab = dial.ShowModal() == wx.ID_YES

		# load diagram in a new page
		diagram = Diagram() if new_tab else canvas.GetDiagram()

		### if diagram is instantiated
		if diagram:
			load_file_result = diagram.LoadFile(filename)

			### if diagram is loaded
			if not isinstance(load_file_result, Exception):

				mainW = canvas.GetTopLevelParent()
				nb2 = mainW.GetDiagramNotebook()

				### if new tab
				if new_tab:
					nb2.AddEditPage(label, diagram)
				else:
					selection = nb2.GetSelection()
					nb2.SetPageText(selection,label)

				# Add as new recent file
				if filename not in mainW.openFileList:
					mainW.openFileList.insert(0, filename)
					del mainW.openFileList[-1]
					mainW.cfg.Write("openFileList", str(eval("mainW.openFileList")))
					mainW.cfg.Flush()

				return True
			else:
				info = _('Error opening file \n file : %s \n object : %s \n error : %s ')%(filename, load_file_result[1], load_file_result[0])
				wx.MessageBox(info, _('Error'), wx.OK|wx.ICON_ERROR)
				return False

class PyComponent:
	""" Return labeled block from filename at (x,y) position in canvas

		@filename: filename for loading block
		@label: label of block
		@x: horizontal position
		@y: vertical position
		@canvas: canvas accepting block
	"""

	@staticmethod
	def Rename(filename:str, new_name:str):
		""" Rename the filename with the new_name.
		"""

		old_bn = os.path.basename(filename)
		dn = os.path.dirname(filename)
		old_name, ext = os.path.splitext(old_bn)
		
		new_filepath = "".join([os.path.join(dn, new_name),ext])

		#read input file
		fin = open(filename, "rt")
		#read file contents to string
		data = fin.read()
		
		if 'class %s(DomainBehavior):'%old_name in data or 'class %s(DomainStructure):'%old_name:
			
			#replace all occurrences of the required string
			data = data.replace(old_name, new_name)
			#close the input file
			fin.close()

			#overrite the input file with the resulting data
			with open(filename, "wt") as fin:
				fin.write(data)
			
			### relace on file system
			os.rename(filename, new_filepath)

			### replace in __init__.py file if exist!
			init_file = os.path.join(dn,'__init__.py')
			if os.path.isfile(init_file):
				replaceAll(init_file, old_name, new_name)

			return True
		else:
			info = _("It seams that the python file dont inherite of the DomainBehavior or DomainStructure classes or \
						its name and the name of the class is different.\n \
						Please correct this aspect before wanted to rename the python file from DEVSimPy.")
			wx.MessageBox(info, _("Error"), wx.OK|wx.ICON_ERROR)
			return False

	@staticmethod
	def Load(filename:str, label:str):
		""" Load python file from filename
		"""
		fn = filename.strip()
	
		assert(fn.endswith(('.py','.pyc','.pyd'))),"File %s is not python file!"%fn

		if os.path.exists(fn):
			return BlockFactory.CreateBlock(python_file = fn, label = label)
		else:
			return None

class GenericComponent:
	"""
	"""
	def __init__(self, *argv, **kwargs):
		""" Constructor.
		"""
		# local copy
		self._canvas = kwargs['canvas'] if 'id' in kwargs else None
		self._x = kwargs.get('x',None)
		self._y = kwargs.get('y',None)
		self._label = kwargs.get('label',None)

		if 'id' in kwargs:
			self._iid = kwargs['id']
		elif self._canvas:
			self._iid = self._canvas.GetDiagram().GetiPortCount()
		else:
			self._iid = 0.0

		if 'id' in kwargs:
			self._oid = kwargs['id']
		elif self._canvas:
			self._oid = self._canvas.GetDiagram().GetoPortCount()
		else:
			self._oid = 0.0

		#self._iid = kwargs['id'] if 'id' in kwargs else self._canvas.diagram.GetiPortCount()
		#self._oid = kwargs['id'] if 'id' in kwargs else self._canvas.diagram.GetoPortCount()

		self._inputs = kwargs.get('inputs',1)
		self._outputs = kwargs.get('outputs',1)
		self._python_file = kwargs['python_file']
		self._model_file = kwargs.get('model_file','')
		self._specific_behavior = kwargs.get('specific_behavior','')

	def Create(self):
		""" Abstract method to create component from attributes.
		"""
		pass

	@staticmethod
	def Load(filename, label, x, y, canvas):
		""" Abstract method to load stored component form filename.
		"""
		pass

	@staticmethod
	def ChekFilename(filename, model):
		""" static method to correct the error occurring when the filename is not corresponding with values of paths
			(model and python) embedded in the .amd (dat file). This error occurs when the user copy and past a .amd model into
			an another directory.
		"""

		### update model if the path of the .amd file (filename) doesn't correspond with the paths contained into the .amd file
		if filename != model.model_path:
			model.model_path = filename
			model.python_path = os.path.join(filename, os.path.basename(model.python_path))
			### save the new config path
			model.SaveFile(filename)

		### if image path is wrong and is .amd model, we find the image into the amd file
		image_path_dirname = os.path.dirname(model.image_path)
		if not os.path.exists(image_path_dirname) and os.path.basename(image_path_dirname) == os.path.basename(model.model_path):
			model.image_path = os.path.join(filename,os.path.basename(model.image_path))
			### save the new config path
			model.SaveFile(filename)

		### check if a filename is needed in args (bad_filename_path_flag)
		### find all word containning 'filename' without considering the casse
		m = [re.match('[a-zA-Z]*filename[_-a-zA-Z0-9]*',s, re.IGNORECASE) for s in model.args]
		filename_list = [a.group(0) for a in [s for s in m if s is not None]]
		### for all filename attr
		for name in filename_list:
			fn = model.args[name]
			### show flag icon on the block only for the file with extension (input file)
			if not os.path.exists(fn) and os.path.splitext(fn)[-1] != '':
				model.bad_filename_path_flag = True

		return model

	@staticmethod
	def Rename(filename:str, new_name:str)->bool:
		""" Rename the filename with the new_name.
		"""
			
		old_bn = os.path.basename(filename)
		dn = os.path.dirname(filename)
		old_name, ext = os.path.splitext(old_bn)
			
		new_filepath = "".join([os.path.join(dn, new_name), ext])

		### extract behavioral python file (from .amd or .cmd) to tempdir 
		### in order to rename it and change the name of contening class
		temp_file = None

		with zipfile.ZipFile(filename) as zf:
			### find all python files
			for file in zf.namelist():
				if file.endswith(".py"):
					r = repr(zf.read(file))
					### first find python file with the same of the archive
					if file.endswith(old_bn):
						#new_bn = os.path.basename(new_filepath)
						temp_file = zf.extract(old_bn, tempfile.gettempdir())
						new_temp_file = temp_file

					### then find a python file that inherite of the DomainBehavior or StructureBehavior class
					elif 'DomainBehavior' in r or 'DomainStructure' in r:

						old_name = os.path.splitext(file)[0]
						
						### first we must change the name of this python file in order to have the same as the archive!
						temp_file = zf.extract(file, tempfile.gettempdir())
						new_temp_file = os.path.join(tempfile.gettempdir(), new_name+'.py')
						### rename temp_file to new_temp_file according to the correspondance between the name of the python file and the name of the archive
						### for exemple C:\Users\Laurent\AppData\Local\Temp\MyOld.py C:\Users\Laurent\AppData\Local\Temp\MyNew.py
						if os.path.isfile(new_temp_file):
							os.remove(new_temp_file)

						os.rename(temp_file, new_temp_file)

		if temp_file:

			### replace in new_temp_file file
			replaceAll(new_temp_file, old_name, new_name)
		
			zip = ZipManager.Zip(filename)
			
			if zip.Delete([os.path.basename(temp_file)]):
				#print("Delete %s"%os.path.basename(temp_file))
				
				#print("Update %s"%new_temp_file)
				zip.Update([new_temp_file])

				#print("rename %s to %s"%(filename,new_filepath))	
			
				### relace on file system
				os.rename(filename, new_filepath)

				return True
			else:
				return False

		else:
			info = _("Please check this: \n \
				The Python filename and the name of archive (%s)) must be egal to the class name!\n \
				Please correct this aspect by extracting the archive.\n")%(old_name)
			wx.MessageBox(info, _("Error"), wx.OK|wx.ICON_ERROR)
			return False
			
class CMDComponent(GenericComponent):
	""" 
	"""

	def __init__(self, *argv, **kwargs):
		""" Constructor.
		"""
		GenericComponent.__init__(self, *argv, **kwargs)

	def Create(self):
		""" Create CMD from constructor.
		"""
		from Container import ContainerBlock, iPort, oPort
		# new containerBlock model
		self.__m = ContainerBlock(self._label, self._inputs, self._outputs)

		# input and output ports
		for id in range(self._inputs):
			iport = iPort(label='IPort %d'%(id))
			iport.id = id
			self.__m.AddShape(iport)
			self.__m.nbiPort = id
			iport.move(50,100*(self.__m.nbiPort))

		for id in range(self._outputs):
			oport = oPort(label='OPort %d'%(id))
			oport.id = id
			self.__m.AddShape(oport)
			self.__m.nboPort = id
			oport.move(300,100*(self.__m.nboPort))

		self.__m.python_path = self._python_file
		self.__m.model_path = self._model_file

		return self.__m

	@staticmethod
	def Load(filename, label):
		""" Load CMD from filename.
		"""
		from Container import ContainerBlock, iPort, oPort
		assert(filename.endswith('.cmd'))

		### new ContainerBlock instance
		m = ContainerBlock()

		load_file_result = m.LoadFile(filename)

		if isinstance(load_file_result, Exception):
			wx.MessageBox(_('Error loading %s model : %s'%(label, str(load_file_result))), _('Error'), wx.OK | wx.ICON_ERROR)
			return None

		else:
			### mandatory due to the LoadFile call before
			m.label = label

			# coupled input ports
			m.input=0 ; m.output=0
			for s in m.shapes:
				if isinstance(s, iPort):
					m.input +=1
				elif isinstance(s, oPort):
					m.output +=1

			return CMDComponent.ChekFilename(filename, m)

class AMDComponent(GenericComponent):
	"""
	"""

	def __init__(self, *argv, **kwargs):
		""" constructor.
		"""
		GenericComponent.__init__(self, *argv, **kwargs)

	def Create(self):
		""" Create AMD from filename.
		"""

		# associated Python class
		cls = GetClass(self._python_file)

		self.__m = AMDComponent.BlockModelAdapter(cls, self._label, self._specific_behavior)

		self.__m.input = self._inputs
		self.__m.output = self._outputs

		### flag is visible only if there are a path extension
		self.__m.bad_filename_path_flag = True in [isinstance(v, str) and os.path.isabs(v) and os.path.splitext(v)[-1] != '' for v in list(self.__m.args.values())]

		self.__m.python_path = self._python_file
		self.__m.model_path = self._model_file

		return self.__m

	@staticmethod
	def Load(filename, label):
		""" Load AMD from constructor.
		"""

		assert(filename.endswith('.amd'))

		python_path = os.path.join(filename, ZipManager.getPythonModelFileName(filename))

		cls = GetClass(python_path)

		m = AMDComponent.BlockModelAdapter(cls, label)
		
		load_file_result = m.LoadFile(filename)
		
		if isinstance(load_file_result, Exception):
			wx.MessageBox(_('Error loading %s model : %s '%(label, load_file_result)), _('Error'), wx.OK | wx.ICON_ERROR)
			return None
		else:
			### mandatory due to the LoadFile call before
			m.label = label
			return AMDComponent.ChekFilename(filename, m)

	@staticmethod
	def BlockModelAdapter(cls, label="", specific_behavior=""):
		""" Return block model considering its class hierarchy
			The implementation depends only of the argument of the class. There is no dependance with the collector module (in comment bellow)
		"""
		from Container import DiskGUI, ScopeGUI, CodeBlock
		#from  Domain.Collector import *
		#if issubclass(cls, QuickScope.QuickScope):
				#m = ScopeGUI(label)
			#elif issubclass(cls, (To_Disk.To_Disk, Messagecollector.Messagecollector)):
				#m = DiskGUI(label)
			#else:
				## mew CodeBlock instance
				#m = CodeBlock()

		# associated python class membre

		clsmbr = getClassMember(inspect.getfile(cls))

		### args of class
		args = GetArgs(cls)

		### find if there is filename param on the constructor and if there is no extention
		L = [os.path.isabs(str(a)) or str(a)=='result' for a in list(args.values())]
		filename_without_ext_flag = L.index(True) if True in L else -1
		### if there is a filename and if there is no extention -> its a to disk like object
		disk_model = filename_without_ext_flag >= 0 and not os.path.splitext(list(args.values())[filename_without_ext_flag])[-1] != ''

		### find if scope is present in class name
		match = [re.match('[-_a-zA-z]*scope[-_a-zA-z]*',s, re.IGNORECASE) for s in list(clsmbr.keys())+[specific_behavior]]
		scope_model = [a.group(0) for a in [s for s in match if s is not None]] != []

		### find if messagecollector is present in class name
		match = [re.match('[-_a-zA-z]*collector[-_a-zA-z]*',s, re.IGNORECASE) for s in list(clsmbr.keys())+[specific_behavior]]
		messagecollector_model = [a.group(0) for a in [s for s in match if s is not None]] != []

		# new codeBlcok instance
		if disk_model or messagecollector_model:
			m = DiskGUI(label)
		elif scope_model:
			m = ScopeGUI(label)
		else:
			m = CodeBlock(label)

		# define behavioral args from python class
		m.args = args

		return m

#---------------------------------------------------------
class DEVSComponent:
	"""
	"""

	def __init__(self):
		""" Constructor.
		"""

		# DEVS instance
		self.devsModel = None

		# path of py file for import process
		self.python_path = ''

		# args of constructor
		self.args = {}

	def __getstate__(self):
		"""Return state values to be pickled."""

		### we copy a new state in order to dont lost the devs result of Scope for example.
		new_state = self.__dict__.copy()

		### delete devs instance (because is generate before the simulation)
		new_state['devsModel'] = None

		### overriding method (coming from plugins) can't be pickled
		for name,value in list(new_state.items()):
			module = inspect.getmodule(value)
			if isinstance(value, types.MethodType):
				new_state[name] = None

		return new_state

	@staticmethod
	def getBlockModel(devs):
		return devs.blockModel

	@staticmethod
	def setBlockModel(devs, block):
		devs.blockModel = block

	@staticmethod
	def debugger(m, msg):
		bm = m.getBlockModel()
		path = os.path.join(gettempdir(),'%s.%d.devsimpy.log'%(str(bm.label), id(bm)))
		
		with open(path,'a') as f:
			try:
				f.write("clock %s: %s\n"%(m.timeNext, msg))
			except Exception:
				f.write("clock %d: %s\n"%(0.0, str(msg)))

	def setDEVSPythonPath(self, python_path:str):
		if os.path.isfile(python_path) or zipfile.is_zipfile(os.path.dirname(python_path)):
			self.python_path = python_path

	def getDEVSPythonPath(self)->str:
		""" Return the DEVS python path.
		"""
		return self.python_path

	def getDEVSModel(self):
		""" Return the DEVS model.
		"""
		return self.devsModel
		
	def setDEVSModel(self, devs):
		"""
		Set the DEVS model.

		@param devs: DEVS coupled model
		@type: instance
		"""
		self.devsModel = devs
		self.setBlock(devs)

	def setDEVSParent(self, p):
		"""
		Set the DEVS parent model.

		@param p: parent
		@type: instance
		"""
		if self.devsModel != None:
			self.devsModel.parent = p

	def getDEVSParent(self):
		"""
		Get the DEVS parent.
		"""
		return self.devsModel.parent if self.devsModel else None

	def getBlock(self):
		"""
		Get the Block.
		"""
		if self.devsModel is not None:
			return DEVSComponent.getBlockModel(self.devsModel)

	def setBlock(self, devs):
		""" 
		Set the Block.
		"""
		if devs is not None:
			### define new methods in order to set and get blockModel from devs instance
			if not hasattr(devs, 'getBlockModel'):
				setattr(devs.__class__, DEVSComponent.getBlockModel.__name__, DEVSComponent.getBlockModel)
				setattr(devs.__class__, DEVSComponent.setBlockModel.__name__, DEVSComponent.setBlockModel)
			### define new method in order to debug devs model
			### user just write msg using debugger method in devs code
			if not hasattr(devs, 'debugger'):
				setattr(devs.__class__, DEVSComponent.debugger.__name__, DEVSComponent.debugger)
			
			if builtins.__dict__.get('GUI_FLAG',True):
				### to execute finish method of devs model (look at the SimulationGUI for message interception)
				if hasattr(devs, 'finish'):
					Publisher.subscribe(devs.finish, "%d.finished"%(id(devs)))

			DEVSComponent.setBlockModel(devs, self)

	###
	def setDEVSClassModel(self, classe):
		""" Set the __class__ attribut of the devs model
			@param classe: new classe object
		"""
		if inspect.isclass(classe):
			self.devsModel.__class__ = classe

	###
	def isCMD(self):
		""" Return True if the python file is embedded in CMD file
		"""
		fn = os.path.dirname(self.getDEVSPythonPath())
		return zipfile.is_zipfile(fn) and fn.endswith(('.cmd')) if os.path.isfile(fn) else False

	###
	def isAMD(self):
		""" Return True if the python file is embedded in AMD file
		"""
		fn = os.path.dirname(self.getDEVSPythonPath())
		return zipfile.is_zipfile(fn) and fn.endswith(('.amd')) if os.path.isfile(fn) else False

	def isPYC(self):
		""" Return True if the python path point to a python file
		"""
		return self.python_path.endswith('.pyc') if os.path.isfile(self.python_path) else False

	def isPY(self):
		""" Return True if the python path point to a compiled python file
		"""
		return self.python_path.endswith('.py') if os.path.isfile(self.python_path) else False

	###
	def OnLog(self, event):
		""" Shows informations inserted with debugger instructions into the model.
		"""

		### devs model, block label, log file in temp dir
		devs = self.getDEVSModel()
		block = devs.getBlockModel()
		label = str(block.label)
		log_file = os.path.join(gettempdir(),'%s.%d.devsimpy.log'%(label,id(block)))
		parent = event.GetClientData()

		if os.path.exists(log_file):
			### read log file
			with open(log_file, 'r') as f:
				msg = f.read()
			
			### show log file content
			#dlg = wx.lib.dialogs.ScrolledMessageDialog(parent, msg, _("%s logger")%label, style=wx.OK|wx.ICON_EXCLAMATION|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
			#dlg.ShowModal()

			frame = FrameEditor(parent, -1, _("%s logger")%label)
			frame.AddText(msg)
			frame.Show()

		else:
			dial = wx.MessageDialog(parent, _("Log is empty.\nIf you want to debug, please use the debugger method."), label, wx.OK|wx.ICON_INFORMATION)
			dial.ShowModal()

	def updateDEVSPriorityList(self):
		""" Update the componentSet order from priority_list for corresponding diagram
		"""
		from Container import ContainerBlock, Diagram, Block
		assert(isinstance(self, (ContainerBlock, Diagram)))

		### if devs instance is not none and priority_list has been invoked (else componentSet order is considered)
		if self.priority_list != []:

			block_list = [c for c in self.GetShapeList() if isinstance(c, Block)]

			label_list = [m.label for m in block_list]

			### added models
			added_models = [l for l in label_list if l not in self.priority_list]

			### removed models
			for label in [l for l in self.priority_list if l not in label_list]:
				index = self.priority_list.index(label)
				del self.priority_list[index]

			self.priority_list += added_models
 
	###
	def OnEditor(self, event):
		""" Method that edit the python code of associated devs model of the Block.
		"""
		from Container import ShapeCanvas

		python_path = self.python_path
		model_path = os.path.dirname(python_path)
		name = os.path.basename(python_path)

		### trying to get parent window
		mainW = GetActiveWindow(event)

		if isinstance(mainW, ShapeCanvas):
			mainW = mainW.GetParent()

		if not builtins.__dict__['LOCAL_EDITOR'] and not zipfile.is_zipfile(model_path) and not python_path.startswith('http'):
			dial = wx.MessageDialog(mainW, _('Do you want to use your local code editor software?\n\n If you always want to always use the local DEVSimPy code editor\n change the option in the Editor panel preference.'), name, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			val = dial.ShowModal()
		else:
			val = wx.ID_YES

		### if local editor
		if val == wx.ID_NO:
			### open with local editor
			if wx.Platform == '__WXMAC__':
				subprocess.call(" ".join(['open -a',python_path]), shell=True)
			elif "wxMSW" in wx.PlatformInfo:
				editor = builtins.__dict__['EXTERNAL_EDITOR_NAME']
				
				### try to import the editor
				try:
					importlib.import_module(editor)
				### if not install it
				except ImportError:
					if BuzyCursorNotification(install(editor)):
						dial = wx.MessageDialog(self.parent, _('You need to restart DEVSimPy to use the %s code editor.')%editor, name, wx.OK | wx.ICON_INFORMATION)
						val = dial.ShowModal()

				### open the editor
				if editor == 'pyzo':
					subprocess.Popen(['pyzo', python_path])
				elif editor == 'spyder':
					subprocess.Popen(['spyder', python_path, '--multithread'])
				
			elif "wxGTK" in wx.PlatformInfo:
				### with gnome
				if os.system('pidof gedit') == 256:
					try:
						soft = which('gedit')
					except:
						sys.stdout.write(_("Local programmer software not found!\n"))
					else:
						subprocess.call(" ".join([soft,python_path]), shell=True)

				### with kde
				elif os.system('pidof ksmserver') == 256:
					try:
						soft = which('kfmclient')
					except:
						sys.stdout.write(_("Local programmer software not found!\n"))
					else:
						os.system(soft+" openURL " + python_path)
				else:
					sys.stdout.write(_("Unknown Windows Manager!\n"))

		elif val != wx.ID_CANCEL:
			# loading file in DEVSimPy editor windows (self.text)
			try:
				
				editorFrame = Editor.GetEditor(None, wx.NewIdRef(), ''.join([name,' - ',model_path]), obj=self, file_type='block')

				# if zipfile.is_zipfile(model_path):
				# 	importer = zipimport.zipimporter(model_path)
				# 	text = importer.get_source(os.path.splitext(name)[0])

				if not zipfile.is_zipfile(model_path):
					### if file is localized on the net
					if python_path.startswith('http'):
						### with internet python file, the editorFrame is read only
						editorFrame.SetReadOnly(True)

						printOnStatusBar(editorFrame.statusbar, {0:_('read only')})

						### parse url to extract the path(/devsimpy/domain...) and the network location (lcapocchi.free.fr)
						o = urlparse(python_path)
						### open connection
						c = httplib.HTTPConnection(o.netloc)
						### request with GET mode
						c.request('GET', o.path)
						### get response of request
						r = c.getresponse()
						### convert file into string
						text = r.read()

					else:

						### if python_path is not found (because have an external origin)
						if not os.path.exists(python_path) and os.path.basename(
						    DOMAIN_PATH) in python_path.split(os.sep):
							python_path = os.path.join(HOME_PATH, python_path[python_path.index(os.path.basename(DOMAIN_PATH)):].strip('[]'))
							self.python_path = python_path

										# ### only with python 2.6
										# with codecs.open(python_path, 'r', 'utf-8') as f:
										# 	text = f.read()

				name = os.path.basename(python_path)

				editorFrame.AddEditPage(name, python_path)
				editorFrame.Show()

				printOnStatusBar(editorFrame.statusbar,{1:''})

				return editorFrame

			except Exception as info:
				dlg = wx.MessageDialog(
				    mainW,
				    _('Editor frame not instanciated: %s\n' % info),
				    name,
				    wx.OK | wx.ICON_ERROR,
				)
				dlg.ShowModal()
				return False

class BlockFactory:
	""" DEVSimPy Block Factory.
	"""

	@staticmethod
	def GetModule(filename):
		""" Give module object from python file path. Warning, the name of python_file must be the same of the classe name.
		"""

		dir_name = os.path.dirname(filename)
		
		### if python_file is ...../toto.amd/Atomic_Model.py, then the parent dir is zipfile.
		if zipfile.is_zipfile(dir_name):
			zf = ZipManager.Zip(dir_name)
			return zf.GetModule()
		elif zipfile.is_zipfile(filename):
			zf = ZipManager.Zip(filename)
			return zf.GetModule()
		### if python file is on the web !
		elif filename.startswith(('http','https')):
			
			net = Net(filename)
			return net.GetModule()
		### pure python file
		else:
		
			### add path to sys.path recursively
			current_dirname = dir_name
			while(current_dirname != os.path.dirname(current_dirname)):
				if current_dirname not in sys.path:
					sys.path.append(current_dirname)
				current_dirname = os.path.dirname(current_dirname)

			module_name = os.path.basename(filename).split('.py')[0]
			name, ext = os.path.splitext(module_name)

			### try to find the specification of module
			spec = importlib.util.find_spec(name, dir_name)
		
			if spec:
				
				### try to import module
				try:
					module = spec.loader.load_module(module_name)
				except (ValueError, ImportError) as msg:
					sys.stderr.write(_("Module %s not imported from %s: %s!\n"%(module_name,dir_name,str(msg))))
					module = sys.exc_info()
				else:
					### if module are finded, we add on sys.modules all of the paths allowing to reach the module 
					### For example, PowerSystem.Sources.SinGen, Sources.SinGen and SinGen is the same module SinGen. So, You can use:
					### from PowerSystem.Sources.SinGen import SinGen
					### from Sources.SinGen import SinGen
					### or SinGen import SinGen

					### replace os.sep by . from DOMAIN_PATH into the path of the python module file
					if DOMAIN_PATH in dir_name:
						L = dir_name.replace(DOMAIN_PATH+os.sep,'').split(os.sep)
						names = ['.'.join(L[i:]+[name]) for i in range(len(L))]
					else:
						### external lib
						### we add the directory of the lib (So, for example, you can import module by using form Dir.module import ... or from module import ...)
						names = ['.'.join([name,module_name])]
					
					### add all combination of path to reach the module
					for n in names:
						sys.modules[n]=module

					### TODO: other dependencies are not imported (python files which are not DomainBehavior or DomainStructure but which are imported from this files...)
					# import pkgutil
					# search_path = [dir_name] # set to None to see all modules importable from sys.path
					# all_modules = [x[1] for x in pkgutil.iter_modules(path=search_path)]
			else:
				sys.stdout.write("Import Error:\n module %s not found\n"%name)
				module = None
					
			return module

	@staticmethod
	def GetBlock(filename, label):
		""" Get Block from filename with (x,y) position in canvas

			@param filename : name of dropped file
			@param label : name of block
			@param x,y : position
			@param canvas: position of block is performed depending on canvas
		"""

		### exclude all chinese character (just for mac)
		if wx.Platform == '__WXMAC__':
			L = re.findall(u'[^\u4E00-\u9FA5]', filename)		
			filename = ''.join(filename)
			
		ext = os.path.splitext(filename)[-1]

		### catch candidtate class from extention
		if ext == '.amd':
			cls = AMDComponent
		elif ext == '.cmd':
			cls = CMDComponent
		else:
			cls = PyComponent

		return cls.Load(filename, label)

	@staticmethod
	def CreateBlock(*argv, **kwargs):
		""" Create Block from python_file and other info coming from wizard.
		"""
		
		from Container import iPort, oPort, MsgBoxError
		### import are here because the simulator (PyDEVS or PyPDEVS) require it
		from DomainInterface.DomainBehavior import DomainBehavior
		from DomainInterface.DomainStructure import DomainStructure

		python_file = kwargs['python_file']
		canvas = kwargs['canvas'] if 'canvas' in kwargs else None
		x = kwargs['x'] if 'x' in kwargs else None
		y = kwargs['y'] if 'y' in kwargs else None

		# associated python class
		cls = GetClass(python_file)
		
  
		if inspect.isclass(cls):
			# adding devs model on good graphical model
			if issubclass(cls, DomainBehavior):
				amd = AMDComponent(*argv, **kwargs)
				m = amd.Create()
				### move AMD model
				if canvas and x and y:
					### convert coordinate depending on the canvas
					x,y = canvas.GetXY(m, x, y)
					# move model from mouse position
					m.move(x, y)
				return m
			elif issubclass(cls, DomainStructure):
				cmd = CMDComponent(*argv, **kwargs)
				m = cmd.Create()
				### move CMD model
				if canvas and x and y:
					### convert coordinate depending on the canvas
					x,y = canvas.GetXY(m, x, y)
					# move model from mouse position
					m.move(x, y)
				return m
			elif  'IPort' in cls.__name__:
				label = kwargs['label']
				iid = kwargs['id'] if 'id' in kwargs else canvas.GetDiagram().GetiPortCount()
				m = iPort(label = "%s %d"%(label,iid))
				m.id = iid
				m.move(x-70, y-70)
				return m
			elif  'OPort' in cls.__name__:
				label = kwargs['label']
				oid = kwargs['id'] if 'id' in kwargs else canvas.GetDiagram().GetoPortCount()
				m = oPort(label = "%s %d"%(label,oid))
				m.id = oid
				m.move(x-70, y-70)
				return m
			else:
				dial = wx.MessageDialog(None, _('Object not instantiated !\n\n Perhaps there is bad imports.'), _('Block Manager'), wx.OK | wx.ICON_EXCLAMATION)
				dial.ShowModal()
				return False

		### inform user of the existance of error and return None
		else:
			MsgBoxError(None, GetActiveWindow(), cls)

		return None
