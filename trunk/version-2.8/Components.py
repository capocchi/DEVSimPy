# -*- coding: utf-8 -*-

"""
Name: Components.py
Brief descritpion: All classes for components
Author(s): L. Capocchi <capocchi@univ-corse.fr>
Version:  1.0
Last modified: 2013.07.04
GENERAL NOTES AND REMARKS:

GLOBAL VARIABLES AND FUNCTIONS:
"""

import os
import sys
import imp
import inspect
import zipfile
import zipimport
import re
import __builtin__
import wx
import codecs
import string
import types
from tempfile import gettempdir

if wx.VERSION_STRING < '2.9':
	from wx.lib.pubsub import Publisher
else:
	from wx.lib.pubsub import pub as Publisher

import Editor
import ZipManager

from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.DomainStructure import DomainStructure
from Utilities import GetActiveWindow, path_to_module
from NetManager import Net

###########################################################
###
### 		GENERAL FUNCTIONS
###
###########################################################

def printOnStatusBar(statusbar, data={}):
	""" Send data on status bar
	"""
	for k,v in data.items():
		statusbar.SetStatusText(v, k)

def getClassMember(python_file = ''):
	""" Get class member from python file
	"""

	module  = BlockFactory.GetModule(python_file)

	if inspect.ismodule(module):
		## classes composing the imported module
		return dict(inspect.getmembers(module, inspect.isclass))
	### exception in module
	else:
		return module

def GetClass(elem):
	""" Get python class from filename.
	"""

	clsmembers = getClassMember(elem)

	if isinstance(clsmembers, dict):
		moduleName = path_to_module(elem)

		for cls in clsmembers.values():
			#print 'sdf', str(cls.__module__), moduleName, str(cls.__module__) in str(moduleName)

			if str(cls.__module__) in str(moduleName):
				return cls
	else:
		return clsmembers

def GetArgs(cls = None):
	""" Get behavioral attribute from python file through constructor class.
	"""

	if inspect.isclass(cls):
		constructor = inspect.getargspec(cls.__init__)
		return dict(zip(constructor[0][1:], constructor[3])) if constructor[3] != None else {}
	else:
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
		""" Load component from filename
		"""
		from Container import Diagram
		#assert(filename.endswith('.dsp'))

		# its possible to use the orignal copy of the droped diagram
		dial = wx.MessageDialog(canvas, _('Do you want to open the orignal diagram in a new tab?'), label, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

		new_tab = dial.ShowModal() == wx.ID_YES

		# load diagram in a new page
		if new_tab:
			diagram = Diagram()
		else:
			diagram = canvas.GetDiagram()

		### if diagram is instanciated
		if diagram:
			load_file_result = diagram.LoadFile(filename)

			### if diagram is loaded
			if not isinstance(load_file_result, Exception):

				mainW = canvas.GetTopLevelParent()
				nb2 = mainW.nb2

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
	""" Return labeled block from filename at (x,y) postion in canvas

		@filename: filename for loading block
		@label: label of block
		@x: horizontal position
		@y: vertical position
		@canvas: canvas accepting block
	"""

	@staticmethod
	def Load(filename, label):
		""" Load python file from filename
		"""
		assert(filename.endswith('.py'))

		return BlockFactory.CreateBlock( python_file = filename, label = label)

class GenericComponent:
	"""
	"""
	def __init__(self, *argv, **kwargs):
		"""
		"""
		# local copy
		self._canvas = kwargs['canvas'] if 'id' in kwargs else None
		self._x = kwargs['x'] if 'x' in kwargs else None
		self._y = kwargs['y'] if 'y' in kwargs else None
		self._label = kwargs['label'] if 'label' in kwargs else None

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

		self._inputs = kwargs['inputs'] if 'inputs' in kwargs else 1
		self._outputs = kwargs['outputs'] if 'outputs' in kwargs else 1
		self._python_file = kwargs['python_file']
		self._model_file = kwargs['model_file'] if 'model_file' in kwargs else ''
		self._specific_behavior = kwargs['specific_behavior'] if 'specific_behavior' in kwargs else ''

	def Create(self):
		""" Create component from attributes
		"""
		pass

	@staticmethod
	def Load(filename, label, x, y, canvas):
		""" Load strored component form filename
		"""
		pass

class CMDComponent(GenericComponent):
	""" Return labeled block from filename at (x,y) postion in canvas

		@filename: filename for loading block
		@label: label of block
		@x: horizontal position
		@y: vertical position
		@canvas: canvas accepting block
	"""

	def __init__(self, *argv, **kwargs):
		""" Constructor
		"""
		GenericComponent.__init__(self, *argv, **kwargs)

	def Create(self):
		""" Create CMD from constructor
		"""
		from Container import ContainerBlock, iPort, oPort
		# new containerBlock model
		self.__m = ContainerBlock(self._label, self._inputs, self._outputs)

		# input and output ports
		for i in xrange(self._inputs):
			self.__m.nbiPort += i
			id = self.__m.nbiPort
			iport = iPort(label='IPort %d'%(id))
			iport.id = id
			self.__m.AddShape(iport)

		for o in xrange(self._outputs):
			self.__m.nboPort += o
			id = self.__m.nboPort
			oport = oPort(label='OPort %d'%(id))
			oport.id = id
			self.__m.AddShape(oport)

		self.__m.python_path = self._python_file
		self.__m.model_path = self._model_file

		return self.__m

	@staticmethod
	def Load(filename, label):
		""" Load CMD from filename
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

			return m

class AMDComponent(GenericComponent):
	""" Return labeled block from filename at (x,y) postion in canvas

		@filename: filename for loading block
		@label: label of block
		@x: horizontal position
		@y: vertical position
		@canvas: canvas accepting block
	"""

	def __init__(self, *argv, **kwargs):
		""" constructor.
		"""
		GenericComponent.__init__(self, *argv, **kwargs)

	def Create(self):
		""" Create AMD from filename
		"""

		# associated python class
		cls = GetClass(self._python_file)

		self.__m = AMDComponent.BlockModelAdapter(cls, self._label, self._specific_behavior)

		self.__m.input = self._inputs
		self.__m.output = self._outputs

		### flag is visible only if there are a path extension
		self.__m.bad_filename_path_flag = True in map(lambda v: isinstance(v, basestring) and os.path.isabs(v) and os.path.splitext(v)[-1] != '', self.__m.args.values())

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

			return m

	@staticmethod
	def BlockModelAdapter(cls, label="", specific_behavior=""):
		""" Return block model concidering its class hierarchie
			The implementation depends only of the argument of the class. There is no dependance with the collector modul (in comment bellow)
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
		L = map(lambda a: os.path.isabs(str(a)), args.values())
		filename_without_ext_flag = L.index(True) if True in L else -1
		### if there is a filename and if there is no extention -> its a to disk like object
		disk_model = filename_without_ext_flag >= 0 and not os.path.splitext(args.values()[filename_without_ext_flag])[-1] != ''

		### find if scope is present in class name
		match = [re.match('[-_a-zA-z]*scope[-_a-zA-z]*',s, re.IGNORECASE) for s in clsmbr.keys()+[specific_behavior]]
		scope_model = map(lambda a: a.group(0), filter(lambda s : s is not None, match)) != []

		### find if messagecollector is present in class name
		match = [re.match('[-_a-zA-z]*collector[-_a-zA-z]*',s, re.IGNORECASE) for s in clsmbr.keys()+[specific_behavior]]
		messagecollector_model = map(lambda a: a.group(0), filter(lambda s : s is not None, match)) != []

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
	""" Editable class
	"""

	def __init__(self):
		""" Constructor of DEVSComponent.
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
		for name,value in new_state.items():
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
		with open(os.path.join(gettempdir(),'%s.devsimpy.log'%str(m.getBlockModel().label)),'a') as f:
			try:
				f.write("clock %s : %s\n"%(m.timeNext, msg))
			except Exception,error:
				f.write("clock %d : %s\n"%(0.0, msg))

	def setDEVSPythonPath(self, python_path):
		if os.path.isfile(python_path) or zipfile.is_zipfile(os.path.dirname(python_path)):
			self.python_path = python_path

	def getDEVSPythonPath(self):
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
		if self.devsModel != None:
			self.devsModel.parent = p

	def getDEVSParent(self):
		return self.devsModel.parent

	def getBlock(self):
		if self.devsModel is not None:
			return DEVSComponent.getBlockModel(self.devsModel)

	def setBlock(self, devs):
		if devs is not None:
			### define new methods in order to set and get blockModel from devs instance
			if not hasattr(devs, 'getBlockModel'):
				setattr(devs.__class__, DEVSComponent.getBlockModel.func_name, DEVSComponent.getBlockModel)
				setattr(devs.__class__, DEVSComponent.setBlockModel.func_name, DEVSComponent.setBlockModel)
			### define new method in order to debug devs model
			### user just write msg using debugger method in devs code
			if not hasattr(devs, 'debugger'):
				setattr(devs.__class__, DEVSComponent.debugger.func_name, DEVSComponent.debugger)

			### to execute finish method of devs model (look at the SimulationGUI for message interseption)
			if hasattr(devs, 'finish'):
				Publisher.subscribe(devs.finish, "%d.finished"%(id(devs)))

			DEVSComponent.setBlockModel(devs, self)

	def setDEVSClassModel(self, classe):
		""" Set the __class__ attribut of the devs model
			@param classe: new classe object
		"""
		if inspect.isclass(classe):
			self.devsModel.__class__ = classe

	###
	def OnLog(self, event):
		"""
		"""

		### devs model, block label, log file in temp dir
		devs = self.getDEVSModel()
		label = str(devs.getBlockModel().label)
		log_file = os.path.join(gettempdir(),'%s.devsimpy.log'%label)
		parent = event.GetClientData()

		if os.path.exists(log_file):
			### read log file
			with open(log_file, 'r') as f:
				msg = f.read()

			### show log file content
			dlg = wx.lib.dialogs.ScrolledMessageDialog(parent, msg, _("%s logger")%label)
			dlg.ShowModal()

		else:
			dial = wx.MessageDialog(parent, _("Log is empty. If you want to debug, please use the debugger method."), label, wx.OK|wx.ICON_INFORMATION)
			dial.ShowModal()

	def updateDEVSPriorityList(self):
		""" update the componentSet order from priority_list for corresponding diagram
		"""
		from Container import ContainerBlock, Diagram, Block
		assert(isinstance(self, (ContainerBlock, Diagram)))

		coupled_devs = self.getDEVSModel()

		### if devs instance is not none and priority_list has been invocked (else componentSet order is considered)
		if coupled_devs is not None and self.priority_list != []:

			shape_list = self.GetShapeList()
			block_list = filter(lambda c: isinstance(c, Block), shape_list)

			label_list = map(lambda m: m.label, block_list)

			### added models
			added_models = filter(lambda l: l not in self.priority_list, label_list)

			### removed models
			for label in filter(lambda l: l not in label_list, self.priority_list):
				index = self.priority_list.index[label]
				del self.priority_list[index]

			self.priority_list += added_models

			# si l'utilisateur n'a pas definit d'ordre de priorité pour l'activation des modèles, on la construit
			coupled_devs.componentSet = map(lambda b: b.getDEVSModel(), map(self.GetShapeByLabel, self.priority_list))

			self.setDEVSModel(coupled_devs)

	###
	def OnEditor(self, event):
		""" Method that edit the python code of associated devs model of the Block
		"""
		from Container import ShapeCanvas

		python_path = self.python_path
		model_path = os.path.dirname(python_path)
		name = os.path.basename(python_path)

		### trying to get parent window
		mainW = GetActiveWindow(event)

		if isinstance(mainW, ShapeCanvas):
			mainW = mainW.GetParent()

		if __builtin__.__dict__['LOCAL_EDITOR'] and not zipfile.is_zipfile(model_path) and not python_path.startswith('http'):
			dial = wx.MessageDialog(mainW, _('Do you want to use your local programmer software?\n\n If you want always use the DEVSimPy code editor\n change the option in Editor panel preferences.'), name, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			val = dial.ShowModal()
		else:
			val = wx.ID_NO

		### si local editor choisi dans les preferences et pas de zip file et pas de fichier provenant du server ftp
		if val == wx.ID_YES:
			### open with local editor
			if wx.Platform == '__WXMAC__':
				os.system("open " + python_path)
			elif "wxMSW" in wx.PlatformInfo:
				os.startfile(python_path)
			elif "wxGTK" in wx.PlatformInfo:
				### on est dans gnome
				if os.system('pidof gnome-session') != 256:
					try:
						soft = which('gnome-open')
					except:
						sys.stdout.write(_("Local programmer software not found!\n"))
					else:
						os.system(soft+" openURL " + python_path)
				### on est dans kde
				elif os.system('pidof ksmserver') != 256:
					try:
						soft = which('kfmclient')
					except:
						sys.stdout.write(_("Local programmer software not found!\n"))
					else:
						os.system(soft+" openURL " + python_path)
				else:
					sys.stdout.write(_("Unknown Windows Manager!\n"))

		elif val != wx.ID_CANCEL:
			# chargement du fichier dans la fenetre d'edition (self.text)
			try:

				editorFrame = Editor.GetEditor(mainW, wx.ID_ANY, name, obj=self, file_type='block')

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
						### open conenction
						c = httplib.HTTPConnection(o.netloc)
						### request with GET mode
						c.request('GET', o.path)
						### get response of request
						r = c.getresponse()
						### convert file into string
						text = r.read()

					else:

						### if python_path is not found (because have an external origine)
						if not os.path.exists(python_path):
							if os.path.basename(DOMAIN_PATH) in python_path.split(os.sep):
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

			except Exception, info:
				dlg = wx.MessageDialog(mainW, _('Editor frame not instanciated: %s\n'%info), name, wx.OK|wx.ICON_ERROR)
				dlg.ShowModal()
				return False

class BlockFactory:
	""" DEVSimPy Block Factory
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

			module_name = os.path.basename(filename).split('.py')[0]

			# find and load module
			try:
				f, fn, description = imp.find_module(module_name, [dir_name])
				module = imp.load_module(module_name, f, fn, description)
				f.close()
				return module

			except Exception, info:
				return sys.exc_info()

	@staticmethod
	def GetBlock(filename, label):
		""" Get Block from filename with (x,y) position in canvas

			@param filename : name of dropped file
			@param label : name of block
			@param x,y : position
			@param canvas: position of block is performed depending on canvas
		"""

		ext = os.path.splitext(filename)[-1]

		### catch candidtate class from extention
		if ext == ".amd":
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
