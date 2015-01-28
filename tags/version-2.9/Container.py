# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Container.py ---
#                     --------------------------------
#                        Copyright (c) 2009
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 10/04/12
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL IMPORT
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

from __future__ import with_statement

import wx
import wx.lib.dragscroller
#import wx.lib.imagebrowser as ib
import wx.lib.dialogs

if wx.VERSION_STRING < '2.9':
	from wx.lib.pubsub import Publisher
else:
	from wx.lib.pubsub import pub as Publisher

from wx.lib.newevent import NewEvent

### wx.color has been removed in wx. 2.9
if hasattr(wx, "Color"):
    wx.Colour = wx.Color
else:
    wx.Color = wx.Colour

import os
import sys
import copy
import inspect
import re
import cPickle
import zipfile
import types
import array

from tempfile import gettempdir
import __builtin__
from traceback import format_exception

from math import * ### for eval

import gettext
_ = gettext.gettext

AttrUpdateEvent, EVT_ATTR_UPDATE = NewEvent()

import DomainInterface.MasterModel
import ConnectDialog
import DiagramConstantsDialog
import SpreadSheet
import PlotGUI
import pluginmanager
import ZipManager
import DropTarget
import SimulationGUI
import PriorityGUI
import CheckerGUI
import PluginsGUI
import WizardGUI
import Components
import Menu
import LabelGUI
#import ReloadModule

### Mixin
from Mixins.Attributable import Attributable
from Mixins.Achievable import Achievable
from Mixins.Resizeable import Resizeable
from Mixins.Rotatable import Rotatable
from Mixins.Connectable import Connectable
from Mixins.Plugable import Plugable
from Mixins.Structurable import Structurable
from Mixins.Savable import Savable
from Mixins.Selectable import Selectable

### for all dsp model build with old version of DEVSimPy
sys.modules['Savable'] = sys.modules['Mixins.Savable']

from Decorators import BuzyCursorNotification, StatusBarNotification, ProgressNotification, Pre_Undo, Post_Undo, cond_decorator
from Utilities import HEXToRGB, RGBToHEX, relpath, GetActiveWindow, playSound, sendEvent, getInstance, FixedList
from Patterns.Observer import Subject, Observer
from DetachedFrame import DetachedFrame
from AttributeEditor import AttributeEditor, QuickAttributeEditor
from PropertiesGridCtrl import PropertiesGridCtrl

#Global Stuff -------------------------------------------------
clipboard = []

PORT_RESOLUTION = True

##############################################################
#                                                            #
# 					GENERAL fUNCTIONS                        #
#                                                            #
##############################################################

def MsgBoxError(event, parent, msg):
	""" Pop-up alert for error in the .py file of a model
	"""

	### if importation error
	if isinstance(msg, unicode):
		dial = wx.MessageDialog(parent, \
							_('Error trying to import module : %s')%msg, \
							_('Error Manager'), \
							wx.OK | wx.ICON_ERROR)
		dial.ShowModal()
	### Error occurring into the constructor or during the simulation
	elif isinstance(msg, tuple):
		### find error info of the error
		try:
			typ, val, tb = msg
			trace = format_exception(typ, val, tb)

			mainW = wx.GetApp().GetTopWindow()

			### try to find if the error come from devs model
			### paths in traceback
			paths = filter(lambda a: a.split(',')[0].strip().startswith('File'), trace)
			### find if DOMAIN_PATH is in paths list (inverted because traceback begin by the end)
			for p in paths[::-1]:
				### find if one path in trace comes from Domain or exported path list
				for d in [DOMAIN_PATH]+mainW.GetExportPathsList():
					if d in p:
						path,line,fct = p.split(',')[0:3]
						break

		except Exception, info:
			path = None
			line = None
			fct = None

		if path is not None:
			python_path = "File: %s\n"%(path.split(' ')[-1])
		else:
			python_path = ""

		if line is not None:
			line_number = "Line: %s\n"%(line.split(' ')[-1])
		else:
			line_number = ""

		if fct is not None:
			fct = "Function: %s\n"%(fct.split('\n')[0])
		else:
			fct = ""

		if path is not None:

			### ask to correct error
			dial = wx.MessageDialog(parent,\
								 _("Error: %s\n%s%s%s\nDo you want to remove this error?")%(str(val),str(python_path),str(fct),str(line_number)),\
								 _('Error Manager'), \
								 wx.YES_NO | wx.YES_DEFAULT | wx.ICON_ERROR)
			if dial.ShowModal() == wx.ID_YES:
				### delete " and cast to string
				python_path = str(path.split(' ')[-1])[1:-1]
				dir_name = os.path.dirname(python_path)
				### create a temporary component to invoke editor windows
				devscomp = Components.DEVSComponent()
				devscomp.setDEVSPythonPath(python_path)
				### instantiation of editor frame and go to the line of the corresponding error
				editor_frame = Components.DEVSComponent.OnEditor(devscomp, event)
				if zipfile.is_zipfile(dir_name): editor_frame.cb.model_path = dir_name
				if editor_frame:
					nb = editor_frame.GetNoteBook()
					page = nb.GetCurrentPage()
					pos = int(line.split(' ')[-1])
					page.GotoLine(pos)

				return True
			else:
				return False
		else:
			wx.MessageBox(_("There is errors in python file.\nError trying to translate error informations: %s %s %s")%(typ, val, tb), _("Error"), wx.OK|wx.ICON_ERROR)

def printOnStatusBar(statusbar, data={}):
	""" Send data on status bar
	"""
	for k,v in data.items():
		statusbar.SetStatusText(v, k)

def CheckClass(m):

	if inspect.isclass(m):
		cls = m
		args = Components.GetArgs(cls)

	elif isinstance(m, Block):
		cls = Components.GetClass(m.python_path)
		args = m.args

	elif os.path.exists(m):
		### if .amd or .cmd
		if zipfile.is_zipfile(m):
			#zf = ZipManager.Zip(m)
			cls = Components.GetClass(os.path.join(m, ZipManager.getPythonModelFileName(m)))
		### .py
		else:
			cls = Components.GetClass(m)

		args = Components.GetArgs(cls)

	elif m.startswith('http'):
		cls = Components.GetClass(m)
		args = Components.GetArgs(cls)

	else:
		cls = ("","","")

	### check cls error
	if isinstance(cls, tuple):
		return cls
	else:

		### check devs instance
		devs = getInstance(cls, args)

		### check instance error
		return devs if isinstance(devs, tuple) else None

################################################################
#                                                              #
# 						GENERAL CLASS                          #
#                                                              #
################################################################

#-------------------------------------------------------------------------------
class Diagram(Savable, Structurable):
	""" Diagram class.
	"""

	def __init__(self):
		""" Constructor.

		"""

		# list of shapes in the diagram
		self.shapes = []

		self.parent = None

		# shape priority for simulation
		self.priority_list = []

		# constants dico
		self.constants_dico = {}

		# devs Master model
		self.devsModel = None

		# list of number of Block and Port under the diagram
		self.nbCodeBlock = 0
		self.nbContainerBlock = 0
		self.nbiPort = 0
		self.nboPort = 0

		# list of deleted id
		self.deletedCodeBlockId = []
		self.deletedContainerBlockId = []
		self.deletediPortId = []
		self.deletedoPortId = []

		self.last_name_saved = ''
		self.modify = False

	def __getstate__(self):
		"""Return state values to be pickled."""

		### we copy a new state in order to dont lost the devs result of Scope for example.
		new_state = self.__dict__.copy()

		### delete devs instance (because is generate before the simulation)
		new_state['devsModel'] = None
		### set parent attribut for undo/redo
		new_state['parent'] = None

		return new_state

	def __getattr__(self, name):
		"""Called when an attribute lookup has not found the attribute in the usual places
		"""

		if name == 'dump_attributes':
			return ['shapes', 'priority_list', 'constants_dico']
		else:
			raise AttributeError, name

	@staticmethod
	def makeDEVSGraph(diagram, D = {}, type = object):
		""" Make a formated dictionnary to make the graph of the DEVS Network : {'S1': [{'C1': (1, 0)}, {'M': (0, 1)}], port 1 of S1 is connected to the port 0 of C1...
		"""


		# for all components in the diagram
		for c in diagram.GetShapeList():
			# if the component is the conncetionShape, then add the new element in the D dictionnary
			if isinstance(c, ConnectionShape):
				model1, portNumber1 = c.input
				model2, portNumber2 = c.output

				# return D with object representation
				if type is object:
					D.setdefault(model2,[]).append({model1: (portNumber2 ,portNumber1)})

					if isinstance(model1, (iPort,oPort)):
						D.setdefault(model1,[]).append({model2: (portNumber1 ,portNumber2)})

				# return D with string representation
				else:
					label1 = model1.label
					label2 = model2.label

					D.setdefault(label2,[]).append({label1: (portNumber2 ,portNumber1)})

					if isinstance(model1, (iPort,oPort)):
						D.setdefault(label1,[]).append({label2: (portNumber1 ,portNumber2)})

			#if the component is a container block achieve the recursivity
			elif isinstance(c, ContainerBlock):
				Diagram.makeDEVSGraph(c,D,type)

		return D

	@staticmethod
	def makeDEVSInstance(diagram = None):
		""" Return the DEVS instance of diagram. iterations order is very important !
				1. we make the codeblock devs instance
				2. we make the devs port instance for all devsimpy port
				3. we make Containerblock instance
				4. we make the connection
		"""

		#ReloadModule.recompile("DomainInterface.DomainBehavior")
		#ReloadModule.recompile("DomainInterface.DomainStructure")
		#ReloadModule.recompile("DomainInterface.MasterModel")

		### PyPDEVS work with this
		#diagram.setDEVSModel(DomainInterface.MasterModel.Master())

		### TODO to be tested with PyPDEVS !!!
#		if isinstance(diagram.parent, ShapeCanvas):
#			diagram.setDEVSModel(DomainInterface.MasterModel.Master())
#		else:
#			diagram.ClearAllPorts()

		### if devs instance of diagram is not instantiated, we make it
		### else one simulation has been performed then we clear all devs port instances
		if diagram.getDEVSModel():
			diagram.ClearAllPorts()
		else:
			diagram.setDEVSModel(DomainInterface.MasterModel.Master())

		### shape list of diagram
		shape_list = diagram.GetShapeList()
		block_list = filter(lambda c: isinstance(c, Block), shape_list)

		### for all codeBlock shape, we make the devs instance
		for m in block_list:

			### class object from python file
			cls = Components.GetClass(m.python_path)

			### Class is wrong ?
			if isinstance(cls, (ImportError, tuple)) or cls is None:
				print _('Error making DEVS instances for:\n%s\n%s'%(str(cls), m.python_path))
				return False
			else:
				### DEVS model recovery
				devs = getInstance(cls, m.args)

				### Is safe instantiation ?
				if isinstance(devs, tuple):
					return devs

			if isinstance(m, CodeBlock):
				### les ports des modeles couples sont pris en charge plus bas dans les iPorts et oPorts
				## ajout des port par rapport aux ports graphiques
				for i in xrange(m.input):
					devs.addInPort('in_%d'%i)

				for i in xrange(m.output):
					devs.addOutPort('out_%d'%i)

			### devs instance setting
			m.setDEVSModel(devs)

			m.setDEVSParent(diagram.getDEVSModel())

			### allow to escape the check of the simulation running in PyPDEVS (src/DEVS.py line 565)
			if hasattr(devs.parent, "fullName"):
				del devs.parent.fullName

			### adding
			diagram.addSubModel(devs)

			#### recursion
			if isinstance(m, ContainerBlock):
				Diagram.makeDEVSInstance(m)

		# for all iPort shape, we make the devs instance
		for m in filter(lambda s: isinstance(s, iPort), shape_list):
			diagram.addInPort()
			assert(len(diagram.getIPorts()) <= diagram.input)

		# for all oPort shape, we make the devs instance
		for m in filter(lambda s: isinstance(s, oPort), shape_list):
			diagram.addOutPort()
			assert(len(diagram.getOPorts()) <= diagram.output)

		### Connection
		for m in filter(lambda s: isinstance(s, ConnectionShape), shape_list):
			m1,n1 = m.input
			m2,n2 = m.output
			if isinstance(m1, Block) and isinstance(m2, Block):
				p1 = m1.getDEVSModel().OPorts[n1]
				p2 = m2.getDEVSModel().IPorts[n2]
			elif isinstance(m1, Block) and isinstance(m2, oPort):
				p1 = m1.getDEVSModel().OPorts[n1]
				p2 = diagram.getDEVSModel().OPorts[m2.id]
			elif isinstance(m1, iPort) and isinstance(m2, Block):
				p1 = diagram.getDEVSModel().IPorts[m1.id]
				p2 = m2.getDEVSModel().IPorts[n2]
			else:
				print _("Error making DEVS connection between %s and %s."%(m1,m2))
				return False

			Structurable.ConnectDEVSPorts(diagram, p1, p2)

		### change priority form priority_list is PriorityGUI has been invoked (Otherwise componentSet oreder is considered)
		diagram.updateDEVSPriorityList()

		return diagram.getDEVSModel()

	def SetParent(self, parent):
		assert isinstance(parent, ShapeCanvas)
		self.parent =  parent

	def GetParent(self):
		return self.parent

	def GetGrandParent(self):
		return self.GetParent().GetParent()

	@cond_decorator(__builtin__.__dict__['GUI_FLAG'], ProgressNotification("DEVSimPy open file"))
	def LoadFile(self, fileName = None):
		""" Function that load diagram from a file.
		"""

		load_file_result = Savable.LoadFile(self, fileName)

		if isinstance(load_file_result, Exception):
			### Exception propagation
			return load_file_result
		else:
			# load constants (like Rs, Lms...) into the general builtin (to use it, <title>['Lms'] into the expr)
			# give title by basename of filename
			title = os.path.splitext(os.path.basename(fileName))[0]
			# load constants into the general builtin
			self.LoadConstants(title)

			for shape in self.GetShapeList():
				self.UpdateAddingCounter(shape)

			return True

	#@cond_decorator(__builtin__.__dict__['GUI_FLAG'], StatusBarNotification('Load'))
	def LoadConstants(self, label):
		""" Load Constants to general builtin.
		"""

		if self.constants_dico != {}:
			__builtin__.__dict__[label] = self.constants_dico

		for s in filter(lambda c: isinstance(c, ContainerBlock), self.GetShapeList()):
			s.LoadConstants(s.label)

	def OnPriority(self, parent):
		""" Method that show the priorityGUI frame in order to define the activation priority of components
		"""

		shapes_list = [s.label for s in self.GetShapeList() if isinstance(s, Block)]

		#list of all components
		if self.priority_list == []:
			self.priority_list = shapes_list
		else:

			### priority list manager
			cpt = 1
			lenght = len(shapes_list)
			result = [None]*lenght
			for s in shapes_list:
				if s in self.priority_list :
					try:
						result[self.priority_list.index(s)]=s
					except:
						pass
				else:
					result[lenght-cpt] = s
					cpt+=1

			self.priority_list = filter(lambda s: s is not None, result)

			self.modify = True
			self.parent.DiagramModified()

		dlg = PriorityGUI.PriorityGUI(parent, wx.ID_ANY, _("Priority Manager"), self.priority_list)
		dlg.Bind(wx.EVT_CLOSE, self.OnClosePriorityGUI)
		dlg.Show()

	def OnInformation(self, event):
		"""
		"""
		stat_dico = self.GetStat()
		msg = ""
		msg += _("Number of atomic devs model: %d\n")%stat_dico['Atomic_nbr']
		msg += _("Number of coupled devs model: %d\n")%stat_dico['Coupled_nbr']
		msg += _("Number of coupling: %d\n")%stat_dico['Connection_nbr']
		msg += _("Number of deep level (description hierarchy): %d\n")%stat_dico['Deep_level']

		dlg = wx.lib.dialogs.ScrolledMessageDialog(self.GetParent(), msg, _("Diagram Information"), style=wx.OK|wx.ICON_EXCLAMATION|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		dlg.ShowModal()

	def OnClosePriorityGUI(self, event):
		""" Method that update the self.priority_list and close the priorityGUI Frame
		"""

		obj = event.GetEventObject()
		self.priority_list = [obj.listCtrl.GetItemText(i) for i in xrange(obj.listCtrl.GetItemCount())]
		obj.Destroy()

		### we can update the devs priority list during the simulation ;-)
		self.updateDEVSPriorityList()

	def OnAddConstants(self, event):
		""" Method that add constant parameters in order to simplify the modling codeBlock model
		"""

		obj = event.GetEventObject()

		### conditional statement only for windows
		win = obj.GetInvokingWindow() if isinstance(obj, wx.Menu) else obj

		### event come from right click on the shapecanvas
		if isinstance(win, ShapeCanvas):
			win = win.GetParent()
			if isinstance(win, DetachedFrame):
				title = win.GetTitle()
			else:
				title = win.GetPageText(win.GetSelection())

		### event come from Main application by the Diagram menu
		else:

			### needed for window
			if not win: win = obj.GetWindow()

			nb2 = win.GetDiagramNotebook()
			title = nb2.GetPageText(nb2.GetSelection())

		dlg = DiagramConstantsDialog.DiagramConstantsDialog(win, wx.ID_ANY, title, self)
		dlg.ShowModal()
		dlg.Destroy()

	@BuzyCursorNotification
	def checkDEVSInstance(self, diagram=None, D={}):
		""" Recursive DEVS instance checker for a diagram.

				@param diagram : diagram instance
				@param D : Dictionary of models with the associated error

		"""
		### shape list of diagram
		shape_list = diagram.GetShapeList()

		#### for all codeBlock and containerBlock shapes, we make the devs instance
		for m in filter(lambda s: isinstance(s, (CodeBlock, ContainerBlock)), shape_list):
			D[m] = CheckClass(m)
			## for all ContainerBlock shape, we make the devs instance and call the recursion
			if isinstance(m, ContainerBlock):
				self.checkDEVSInstance(m, D)

	def DoCheck(self):
		""" Check all models for validation
			Return None if all models are ok, D else
		"""
		### dictionary composed by key = label of model and value = None if no error, exc_info() else
		D = {}
		self.checkDEVSInstance(self, D)
		return D if filter(lambda m: m != None, D.values()) != [] else None

	def OnCheck(self, event):
		""" Check button has been clicked. We check if models which compose the diagram are valide.
		"""
		### if there are models in diagram
		if self.GetCount() != 0:

			obj = event.GetEventObject()
			win = obj.GetTopLevelParent() if isinstance(obj, wx.ToolBar) else obj.GetWindow()

			D = self.DoCheck()
            ### if there is no error
 			if D is None:
				dial = wx.MessageDialog(win,
										_('All DEVS model has been instantiated without error.\n\nDo you want simulate?'),
										_('Error Manager'),
										wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)

				if dial.ShowModal() == wx.ID_YES:
					self.OnSimulation(event)
			else:
				frame = CheckerGUI.CheckerGUI(win, D)
				frame.Show()

		### no models in diagram
		else:
			wx.MessageBox(_("Diagram is empty.\n\nPlease, drag-and-drop model from libraries control panel to build a diagram."),_('Error Manager'))

	def OnSimulation(self, event):
		""" Method calling the simulationGUI
		"""

        ### if there are models in diagram
		if self.GetCount() != 0 :

			## window that contain the diagram which will be simulate
			win = wx.GetApp().GetTopWindow()
			obj = event.GetEventObject()

#			obj = event.GetEventObject()
#			win = obj.GetWindow() if isinstance(obj, wx.Menu) else obj.GetTopLevelParent()

			# diagram which will be simulate
			diagram = self

			D = self.DoCheck()

			### if there is no error in models
 			if D is not None:
				playSound(SIMULATION_ERROR_SOUND_PATH)
				dial = wx.MessageDialog(win, \
									_("There is errors in some models.\n\nDo you want to execute the error manager ?"), \
									_('Simulation Manager'), \
									wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
				if dial.ShowModal() == wx.ID_YES:
					frame = CheckerGUI.CheckerGUI(win, D)
					frame.Show()

				return False

			else:

				### Check if models have the same label
				L = diagram.GetLabelList([])
				if len(L)!=len(set(L)):
					wx.MessageBox(_("It seems that models have same label.\nIf you plan to use Flat simulation algorithm, all model must have a unique label."), _("Simulation Manager"))

				### set the name of diagram
				if isinstance(win, DetachedFrame):
					title  = win.GetTitle()
				else:
					nb2 = win.GetDiagramNotebook()
					title =nb2.GetPageText(nb2.GetSelection()).rstrip()

				diagram.label = os.path.splitext(os.path.basename(title))[0]

				## delete all attached devs instances
				diagram.Clean()

				## make DEVS instance from diagram
				master = Diagram.makeDEVSInstance(diagram)

				## test of filename model attribute
				if all(model.bad_filename_path_flag for model in filter(lambda m: isinstance(m, Block), diagram.GetShapeList()) if hasattr(model, 'bad_filename_path_flag')):
					dial = wx.MessageDialog(win, \
										_("You don't make the simulation of the Master model.\nSome models have bad fileName path !"),\
										_('Simulation Manager'), \
										wx.OK | wx.ICON_EXCLAMATION)
					dial.ShowModal()
					return False

				else:

#					pluginmanager.trigger_event('START_DIAGRAM', parent = win, diagram = diagram)

					### clear all log file
					for fn in filter(lambda f: f.endswith('.devsimpy.log'), os.listdir(gettempdir())):
						os.remove(os.path.join(gettempdir(),fn))

##					obj = event.GetEventObject()
					# si invocation à partir du bouton dans la toolBar (apparition de la frame de simulation dans une fenetre)
					if isinstance(obj, wx.ToolBar) or 'Diagram' in obj.GetTitle():
						frame = SimulationGUI.SimulationDialog(win, wx.ID_ANY, _(" %s Simulator"%diagram.label), master)
						frame.Show()
					## si invocation par le menu (apparition de la frame de simulation dans le panel)
					elif isinstance(obj, (wx.Menu, wx.Frame)):
						sizer3 = wx.BoxSizer(wx.VERTICAL)
						win.panel3.Show()
						win.SimDiag = SimulationGUI.SimulationDialog(win.panel3, wx.ID_ANY, _("Simulation Manager"), master)
						sizer3.Add(win.SimDiag, 0, wx.EXPAND)
						win.panel3.SetSizer(sizer3)
						win.panel3.SetAutoLayout(True)
						### title is Simulation because it must ne the same of the submenu in toolbar (for checking update)
						nb1 = win.GetControlNotebook()
						nb1.InsertPage(2, win.panel3, _("Simulation"), imageId = 2)
					else:
						sys.stdout.write(_("This option has not been implemented yet."))
						return False

				return True
		else:
			wx.MessageBox(_("Diagram is empty. \nPlease, drag-and-drop model from libraries control panel to build a diagram."),_('Simulation Manager'))
			return False

	def AddShape(self, shape, after = None):
		""" Method that insert shape into the diagram at the position 'after'
		"""

		index = self.shapes.index(after) if after else 0
		self.UpdateAddingCounter(shape)
		self.InsertShape(shape, index)

	def InsertShape(self, shape, index = 0):
		""" Method that insert shape into the diagram to the index position
		"""

		self.shapes.insert(index, shape)
		self.modify = True
		if self.parent:
			self.parent.DiagramModified()

	def DeleteShape(self, shape):
		""" Method that delete all shape links
		"""

		### delete all shape connected with connection shape
		for cs in filter(lambda c: isinstance(c, ConnectionShape), self.GetShapeList()):
			if cs.input is not None and cs.output is not None:
				if shape in cs.input+cs.output:
					self.shapes.remove(cs)

		if isinstance(shape, Block):
			if shape.label in self.priority_list:
				### update priority list
				self.priority_list.remove(shape.label)

		try:
			### delete shape
			self.shapes.remove(shape)
		except ValueError:
			sys.stdout.write(_("Error trying to remove %s")%shape)

		### update the number of shape depending to its type
		self.UpdateRemovingCounter(shape)

		self.modify = True
		self.parent.DiagramModified()

	def UpdateRemovingCounter(self, shape):
		""" Method that update the removed shape counter
		"""

		# update number of components
		if isinstance(shape, CodeBlock):
			self.deletedCodeBlockId.append(shape.id)
			self.nbCodeBlock-=1
		elif isinstance(shape, ContainerBlock):
			self.deletedContainerBlockId.append(shape.id)
			self.nbContainerBlock-=1
		elif isinstance(shape, iPort):
			self.deletediPortId.append(shape.id)
			self.nbiPort-=1
		elif isinstance(shape, oPort):
			self.deletedoPortId.append(shape.id)
			self.nboPort-=1
		else:
			pass

	def UpdateAddingCounter(self, shape):
		""" Method that update the added shape counter
		"""

		# gestion du nombre de shape
		if isinstance(shape, CodeBlock):
			shape.id=self.GetCodeBlockCount()
			self.nbCodeBlock+=1
		elif isinstance(shape, ContainerBlock):
			shape.id=self.GetContainerBlockCount()
			self.nbContainerBlock+=1
		elif isinstance(shape, iPort):
			self.nbiPort+=1
		elif isinstance(shape, oPort):
			self.nboPort+=1
		else:
			pass

	def update(self, concret_subject = None):
		""" Update method is invoked by notify method of Subject class
		"""

		### update shapes list in diagram with a delete of connexionShape which no longer exists (when QuickAttributeEditor change input or output of Block)
		csList = filter(lambda a: isinstance(a, ConnectionShape), self.shapes)

		for cs in csList:
			index = cs.output[1]
			model = cs.output[0]
			### if index+1 is superiror to the new number of port (model.input)
			if index+1 > model.input:
				self.DeleteShape(cs)

			index = cs.input[1]
			model = cs.input[0]
			### if index+1 is superiror to the new number of port (model.output)
			if index+1 > model.output:
				self.DeleteShape(cs)

	def PopShape(self,index=-1):
		""" Function that pop the shape at the index position
		"""

		return self.shapes.pop(index)

	def DeleteAllShapes(self):
		""" Method that delete all shapes
		"""

		del self.shapes[:]

		self.modify = True
		self.parent.DiagramModified()

	def ChangeShapeOrder(self, shape, pos=0):
		"""
		"""

		self.shapes.remove(shape)
		self.shapes.insert(pos,shape)

	def GetCount(self):
		""" Function that return the number of shapes that composed the diagram
		"""

		return len(self.shapes)

	def GetFlatBlockShapeList(self, l=[]):
		""" Get the flat list of Block shape using recursion process
		"""

		for shape in self.shapes:
			if isinstance(shape, CodeBlock):
				l.append(shape)
			elif isinstance(shape, ContainerBlock):
				l.append(shape)
				shape.GetFlatBlockShapeList(l)
		return l

	def GetShapeByLabel(self, label=''):
		""" Function that return the shape instance from its label
		"""

		for m in self.GetFlatBlockShapeList():
			if m.label == label:
				return m

		#sys.stderr.write(_("Block %s not found.\n"%(label)))
		return False

	def GetShapeList(self):
		""" Function that return the shapes list
		"""

		return self.shapes

	def GetBlockCount(self):
		""" Function that return the number of Block shape
		"""

		return self.GetCodeBlockCount()+self.GetContainerBlockCount()

	def GetCodeBlockCount(self):
		""" Function that return the number of codeBlock shape
		"""

		if self.deletedCodeBlockId != []:
			return self.deletedCodeBlockId.pop()
		else:
			return self.nbCodeBlock


	def GetContainerBlockCount(self):
		""" Function that return the number of containerBlock shape
		"""

		if self.deletedContainerBlockId != []:
			return self.deletedContainerBlockId.pop()
		else:
			return self.nbContainerBlock


	def GetiPortCount(self):
		""" Function that return the number of iPort shape
		"""

		if self.deletediPortId != []:
			return self.deletediPortId.pop()
		else:
			return self.nbiPort


	def GetoPortCount(self):
		""" Function that return the number of oPort shape
		"""

		if self.deletedoPortId != []:
			return self.deletedoPortId.pop()
		else:
			return self.nboPort

	def Clean(self):
		""" Clean DEVS instances attached to all block model in the diagram.
		"""

		try:

			for devs in filter(lambda a: hasattr(a, 'finish'), self.devsModel.componentSet):
				Publisher.unsubscribe(devs.finish, "%d.finished"%(id(devs)))

			self.devsModel.componentSet = []
		except AttributeError:
			pass

		for m in self.GetShapeList():

			m.setDEVSModel(None)

			if isinstance(m, ConnectionShape):
				m.input[0].setDEVSModel(None)
				m.output[0].setDEVSModel(None)

			if isinstance(m, ContainerBlock):
				m.Clean()

	def GetStat(self, d={'Atomic_nbr':0, 'Coupled_nbr':0, 'Connection_nbr':0, 'Deep_level':0}):
		""" Get information about diagram like the numbe rof atomic model or the number of link between models.
		"""

		first_coupled = False
		for m in self.GetShapeList():
			if isinstance(m, CodeBlock):
				d['Atomic_nbr']+=1
			elif isinstance(m, ContainerBlock):
				d['Coupled_nbr']+=1
				if not first_coupled:
					first_coupled = True
					d['Deep_level']+= 1
				m.GetStat(d)
			elif isinstance(m, ConnectionShape):
				d['Connection_nbr']+=1

		return d

	def GetLabelList(self, l=[]):
		""" Get Labels of all models
		"""

		for m in self.GetShapeList():
			if isinstance(m, CodeBlock):
				l.append(m.label)
			elif isinstance(m, ContainerBlock):
				l.append(m.label)
				m.GetLabelList(l)
		return l

# Generic Shape Event Handler---------------------------------------------------
class ShapeEvtHandler:
	""" Handler class
	"""

	def OnLeftUp(self,event):
		pass

	def OnLeftDown(self,event):
		pass

	def leftUp(self,event):
		pass

	def OnLeftDClick(self,event):
		pass

	def OnRightUp(self,event):
		pass

	def OnRightDown(self,event):
		pass

	def OnRightDClick(self,event):
		pass

	def OnSelect(self,event):
		pass

	def OnDeselect(self,event):
		pass

	def OnMove(self,event):
		pass

	def OnResize(self,event):
		pass

	def OnConnect(self,event):
		pass

# Generic Graphic items---------------------------------------------------------
class Shape(ShapeEvtHandler):
	""" Shape class
	"""

	def __init__(self, x=[], y=[]):
		""" Constructor
		"""

		self.x = array.array('d',x)                      # list of x coord
		self.y = array.array('d',y)                      # list of y coords
		self.fill= ['#add8e6']          # fill color
		self.pen = [self.fill[0] , 1, wx.SOLID]   # pen color and size
		self.font = [FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, u'Arial']

	def draw(self, dc):
		""" Draw method
		"""

		r, g, b = HEXToRGB(str(self.fill[0]))
		brushclr = wx.Color(r, g, b, 128)   # half transparent

		try:
			dc.SetPen(wx.Pen(self.pen[0], self.pen[1], self.pen[2]))
		### for old model
		except:
			dc.SetPen(wx.Pen(self.pen[0], self.pen[1]))

		dc.SetBrush(wx.Brush(brushclr))

		try:
			### adapt size font depending on the size of label
			### begin with the max of font size (defined in preferences)
			font = FONT_SIZE
			### set the font in the dc in order to performed GetTextExtent
			dc.SetFont(wx.Font(font, self.font[1], self.font[2], self.font[3], False, self.font[4]))
			width_t, height_t = dc.GetTextExtent(self.label)
			### size of shape
			width_s = self.x[1]-self.x[0]
			### while the label with is sup of shape width, we reduce the font of the dc (thus the label size)
			while(width_t > width_s):
				font -=1
				dc.SetFont(wx.Font(font, self.font[1], self.font[2], self.font[3], False, self.font[4]))
				width_t, height_t = dc.GetTextExtent(self.label)

			### update the font
			self.font[0]=font

		except Exception:
			try:
				dc.SetFont(wx.Font(10, self.font[1], self.font[2], self.font[3], False, self.font[4]))
			except Exception:
				dc.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, False, u'Arial'))

	def move(self,x,y):
		""" Move method
		"""
		if not self.lock_flag:
			self.x = array.array('d',map((lambda v: v+x), self.x))
			self.y = array.array('d',map((lambda v: v+y), self.y))

	#def OnResize(self):
	#	""" Resize method controled by ResizeNode move method
	#	"""
	#	### dynamic font size with 1O (pointSize) * width (pourcent)/ 100
	#	self.font[0] = int(FONT_SIZE * (self.x[1]-self.x[0]) / 100.0)
	#	pass

	def lock(self):
		self.lock_flag = True

	def unlock(self):
		self.lock_flag = False

	def Copy(self):
		""" Function that return the deep copy of shape
		"""
		return copy.deepcopy(self)

#-------------------------------------------------------------------------------
class LineShape(Shape):
	"""
	"""

	def __init__(self, x1 = 20, y1 = 20, x2 = 50, y2 = 50):
		""" Cosntructor
		"""

		Shape.__init__(self, [x1, x2] ,  [y1, y2])

	def draw(self, dc):
		""" Draw method
		"""

		Shape.draw(self, dc)
		dc.DrawLine(self.x[0], self.y[0], self.x[1], self.y[1])

	def HitTest(self, x, y):
		""" Hitest method
		"""
		if x < min(self.x)-3:return False
		if x > max(self.x)+3:return False
		if y < min(self.y)-3:return False
		if y > max(self.y)+3:return False

		top = (x-self.x[0]) *(self.x[1] - self.x[0]) + (y-self.y[0])*(self.y[1]-self.y[0])
		distsqr = pow(self.x[0]-self.x[1], 2)+pow(self.y[0]-self.y[1],2)
		u = float(top)/float(distsqr)

		newx = self.x[0] + u*(self.x[1]-self.x[0])
		newy = self.y[0] + u*(self.y[1]-self.y[0])

		dist = pow(pow(newx-x, 2) + pow(newy-y, 2), .5)

		return False if dist > 7 else True

#-------------------------------------------------------------------------------
class RoundedRectangleShape(Shape):
	"""     RoundedRectangleShape class
	"""

	def __init__(self, x1 = 20, y1 = 20, x2 = 120, y2 = 120):
		""" constructor
		"""
		Shape.__init__(self, [x1, x2] ,  [y1, y2])

	def draw(self, dc):
		""" Draw method
		"""

		Shape.draw(self,dc)

		width,height=int(self.x[1]-self.x[0]), int(self.y[1]-self.y[0])
		x,y=int(self.x[0]), int(self.y[0])

		### Prepare label drawing
		rect = wx.Rect(x,y, width, height)
		r=4.0
		dc.DrawRoundedRectangleRect(rect, r)

	#def GetRect(self):
		#width,height=int(self.x[1]-self.x[0]), int(self.y[1]-self.y[0])
		#return wx.Rect(self.x[0], self.y[0], width, height)

	def HitTest(self, x, y):
		""" Hitest method
		"""
		if x < self.x[0]: return False
		if x > self.x[1]: return False
		if y < self.y[0]: return False
		if y > self.y[1]: return False

		return True

#-------------------------------------------------------------------------------
class RectangleShape(Shape):
	""" RectangleShape class
	"""

	def __init__(self,x = 20, y = 20, x2 = 120, y2 = 120):
		""" Constructor
		"""

		Shape.__init__(self, [x,x2] ,  [y,y2])

	def draw(self,dc):
		""" Draw paint method
		"""

		Shape.draw(self,dc)
		x,y = int(self.x[0]), int(self.y[0])
		width, height = int(self.x[1]-self.x[0]), int(self.y[1]-self.y[0])
		dc.DrawRectangle(x, y, width, height)

	def HitTest(self, x, y):
		""" Hitest method
		"""

		if x < self.x[0]: return False
		if x > self.x[1]: return False
		if y < self.y[0]: return False
		if y > self.y[1]: return False

		return True

#-------------------------------------------------------------------------------
class PolygonShape(Shape):
	""" PolygonShape class
	"""
	def __init__(self,x = 20, y = 20, x2 = 120, y2 = 120):
		""" Constructor
		"""

		Shape.__init__(self, [x,x2] , [y,y2])

	def draw(self, dc):
		"""
		"""

		Shape.draw(self, dc)

#               dx = (self.x[1]-self.x[0])/2
		dy = (self.y[1]-self.y[0])/2
		p0 = wx.Point(self.x[0],self.y[0]-dy/2)
		p1 = wx.Point(self.x[0],self.y[1]+dy/2)
		p2 = wx.Point(self.x[1], self.y[0]+dy)
		offsetx = (self.x[1]-self.x[0])/2

		dc.DrawPolygon((p0,p1,p2),offsetx)

	def HitTest(self, x, y):
		""" Hitest method
		"""

		if x < self.x[0]: return False
		if x > self.x[1]: return False
		if y < self.y[0]: return False
		if y > self.y[1]: return False
		return True

#-------------------------------------------------------------------------------
class CircleShape(Shape):
	def __init__(self,x=20, y=20, x2=120, y2=120, r=30.0):
		Shape.__init__(self, [x,x2], [y,y2])
		self.r = r

	def draw(self,dc):
		Shape.draw(self,dc)
		dc.SetFont(wx.Font(10, self.font[1],self.font[2], self.font[3], False, self.font[4]))
		dc.DrawCircle(int(self.x[0]+self.x[1])/2, int(self.y[0]+self.y[1])/2, self.r)
		dc.EndDrawing()

	def HitTest(self, x, y):
		if x < self.x[0]: return False
		if x > self.x[1]: return False
		if y < self.y[0]: return False
		if y > self.y[1]: return False
		return True

#-------------------------------------------------------------------------------
class PointShape(Shape):
	def __init__(self, x=20, y=20, size=4, type='rect'):
		Shape.__init__(self, [x] , [y])
		self.type = type
		self.size = size

		if self.type=='rondedrect':
			self.graphic = RoundedRectangleShape(x-size,y-size,x+size,y+size)
		elif self.type=='rect':
			self.graphic = RectangleShape(x-size,y-size,x+size,y+size)
		elif self.type=='circ':
			self.graphic = CircleShape(x-size,y-size,x+size,y+size, size)
		elif self.type=='poly':
			self.graphic = PolygonShape(x-size,y-size,x+size,y+size)

		self.graphic.pen = self.pen
		self.graphic.fill = self.fill

	def moveto(self,x,y):
		"""
		"""
		self.x = x
		self.y = y
		size = self.size

		self.graphic.x = [x-size, x+size]
		self.graphic.y = [y-size, y+size]

	def move(self,x,y):
		"""
		"""
		self.x = array.array('d', map((lambda v: v+x), self.x))
		self.y = array.array('d', map((lambda v: v+y), self.y))
		self.graphic.move(x,y)

	def HitTest(self, x, y):
		return self.graphic.HitTest(x,y)

	def draw(self,dc):
		self.graphic.pen = self.pen
		self.graphic.fill = self.fill
		self.graphic.draw(dc)

#-------------------------------------------------------------------------------
class ShapeCanvas(wx.ScrolledWindow, Subject):
	""" ShapeCanvas class.
	"""

	ID = 0
	CONNECTOR_TYPE = 'direct'

	def __init__(self,\
				 parent,\
	  			id=wx.ID_ANY, \
			  	pos=wx.DefaultPosition, \
		  		size=(-1,-1), \
			  	style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN, \
			  	name="", \
			  	diagram = None):
		""" Construcotr
		"""
		wx.ScrolledWindow.__init__(self, parent, id, pos, size, style, name)
		Subject.__init__(self)

		self.SetBackgroundColour(wx.WHITE)

		self.name = name
		self.parent = parent
		self.diagram = diagram
		self.nodes = []
		self.currentPoint = [0, 0] # x and y of last mouse click
		self.selectedShapes = []
		self.scalex = 1.0
		self.scaley = 1.0
		self.SetScrollbars(50, 50, 50, 50)
		ShapeCanvas.ID += 1

		# Ruber Band Attributs
		self.overlay = wx.Overlay()
		self.permRect = None
		self.selectionStart = None

		self.timer = wx.Timer(self, wx.NewId())
		self.f = None

		self.scroller = wx.lib.dragscroller.DragScroller(self)

		self.stockUndo = FixedList(NB_HISTORY_UNDO)
		self.stockRedo = FixedList(NB_HISTORY_UNDO)

		### subject init
		self.canvas = self

		### attach canvas to notebook 1 (for update)
		try:
			self.__state = {}
			mainW = self.GetTopLevelParent()
			mainW = isinstance(mainW, DetachedFrame) and wx.GetApp().GetTopWindow() or mainW

			self.attach(mainW.GetControlNotebook())

		except AttributeError:
			sys.stdout.write(_('ShapeCanvas not attached to notebook 1\n'))

		## un ShapeCanvas est Dropable
		dt = DropTarget.DropTarget(self)
		self.SetDropTarget(dt)

		#Window Events
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

		#Mouse Events
		self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
		self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
		self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)

		self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
		self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
		self.Bind(wx.EVT_RIGHT_DCLICK, self.OnRightDClick)

		self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleDown)
		self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleUp)

		self.Bind(wx.EVT_MOTION, self.OnMotion)
		self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
		self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

		#Key Events
		self.Bind(wx.EVT_KEY_DOWN, self.keyPress)

		### for quickattribute
		wx.EVT_TIMER(self, self.timer.GetId(), self.OnTimer)

		#wx.CallAfter(self.SetFocus)

		###----------------------------------------------------------------
		#self.bg_bmp = wx.Bitmap(os.path.join("/tmp", 'fig1.png'),wx.BITMAP_TYPE_ANY)

		#self.hwin = HtmlWindow(self, -1, size=(1000,1000))
		#irep = self.hwin.GetInternalRepresentation()
		#self.hwin.SetSize((irep.GetWidth()+25, irep.GetHeight()+100))
		#self.hwin.LoadPage("./html/mymap.html")

		#wx.EVT_IDLE( self, self.OnShow )
		#self.flag = 0
		###------------------------------------------------------------------

		#wx.EVT_SCROLLWIN(self, self.OnScroll)

	#def OnShow( self, event ):
		#if self.flag == 0:
			##self.hwin.LoadFile("html/mymap.html")
			#self.hwin.LoadPage("http://www.google.fr")
			#self.flag = 1

	@Post_Undo
	def AddShape(self, shape, after = None):
		self.diagram.AddShape(shape, after)
		self.UpdateShapes([shape])

	def InsertShape(self, shape, index = 0):
		self.diagram.InsertShape(shape, index)

	@Post_Undo
	def DeleteShape(self, shape):
		self.diagram.DeleteShape(shape)

	def RemoveShape(self, shape):
		self.diagram.DeleteShape(shape)

	@Post_Undo
	def keyPress(self, event):
		"""
		"""

		key = event.GetKeyCode()
		controlDown = event.CmdDown()
		altDown = event.AltDown()
		shiftDown = event.ShiftDown()

		if key == 316:  # right
			move = False
			step = 1 if controlDown else 10
			for m in self.getSelectedShapes():
				m.move(step, 0)
				move = True
				if not self.diagram.modify:
					self.diagram.modify = True
			if not move: event.Skip()
		elif key == 314:  # left
			move = False
			step = 1 if controlDown else 10
			for m in self.getSelectedShapes():
				m.move(-step, 0)
				move = True
				if not self.diagram.modify:
					self.diagram.modify = True
			if not move: event.Skip()
		elif key == 315:  # -> up
			move = False
			step = 1 if controlDown else 10
			for m in self.getSelectedShapes():
				m.move(0, -step)
				move = True
				if not self.diagram.modify:
					self.diagram.modify = True
			if not move: event.Skip()
		elif key == 317:  # -> down
			move = False
			step = 1 if controlDown else 10
			for m in self.getSelectedShapes():
				m.move(0, step)
				move = True
				if not self.diagram.modify:
					self.diagram.modify = True
			if not move: event.Skip()
		elif key == 90 and controlDown and not shiftDown:  # Undo

			mainW = self.GetTopLevelParent()
			tb = mainW.FindWindowByName('tb')

			### find the tool from toolBar thanks to id
			for tool in mainW.tools:
				if tool.GetId() == wx.ID_UNDO:
					button = tool
					break

			if tb.GetToolEnabled(wx.ID_UNDO):
				### send commandEvent to simulate undo action on the toolBar
				sendEvent(tb, button, wx.CommandEvent(wx.EVT_TOOL.typeId))

			event.Skip()
		elif key == 90  and controlDown and shiftDown:# Redo

			mainW = self.GetTopLevelParent()
			tb = mainW.FindWindowByName('tb')

			### find the tool from toolBar thanks to id
			for tool in mainW.tools:
				if tool.GetId() == wx.ID_REDO:
					button = tool
					break

			if tb.GetToolEnabled(wx.ID_REDO):
				### send commandEvent to simulate undo action on the toolBar
				sendEvent(tb, button, wx.CommandEvent(wx.EVT_TOOL.typeId))
			event.Skip()
		elif key == 127:  # DELETE
			self.OnDelete(event)
			event.Skip()
		elif key == 67 and controlDown:  # COPY
			self.OnCopy(event)
			event.Skip()
		elif key == 86 and controlDown:  # PASTE
			self.OnPaste(event)
			event.Skip()
		elif key == 88 and controlDown:  # CUT
			self.OnCut(event)
			event.Skip()
		elif key == 65 and controlDown:  # ALL
			for item in self.diagram.shapes:
				self.select(item)
			event.Skip()
		elif key == 82 and controlDown:  # Rotate model on the right
			for s in filter(lambda shape: not isinstance(shape, ConnectionShape), self.selectedShapes):
				s.OnRotateR(event)
			event.Skip()
		elif key == 76 and controlDown:  # Rotate model on the left
			for s in filter(lambda shape: not isinstance(shape, ConnectionShape), self.selectedShapes):
				s.OnRotateL(event)
			event.Skip()
		elif key == 9: # TAB
			if len(self.diagram.shapes) == 0:
				event.Skip()
				return
			shape = self.select()
			if shape:
				ind = self.diagram.shapes.index(shape[0])
				self.deselect()
				try:
					self.select(self.diagram.shapes[ind+1])
				except:
					self.select(self.diagram.shapes[0])
			else:
				self.select(self.diagram.shapes[0])
			event.Skip()
		else:
			event.Skip()

		self.Refresh()

	def getWidth(self):
		"""
		"""
		return self.GetSize()[0]

	def getHeight(self):
		"""
		"""
		return self.GetSize()[1]

	def DoDrawing(self, dc):
		"""
		"""

		dc.SetUserScale(self.scalex, self.scaley)

		for item in self.diagram.shapes + self.nodes:
			try:
				item.draw(dc)
			except Exception, info:
				sys.stderr.write(_("Draw error: %s \n")%info)

	def OnEraseBackground(self, evt):
		"""
			Handles the wx.EVT_ERASE_BACKGROUND event
		"""

		# This is intentionally empty, because we are using the combination
        # of wx.BufferedPaintDC + an empty OnEraseBackground event to
        # reduce flicker
		pass

		#dc = evt.GetDC()
		#if not dc:
			#dc = wx.ClientDC(self)
			#rect = self.GetUpdateRegion().GetBox()
			#dc.SetClippingRect(rect)

	def OnPaint(self, event):
		"""
		"""

		#pdc = wx.PaintDC(self)

		# If you want to reduce flicker, a good starting point is to
        # use wx.BufferedPaintDC.
		pdc = wx.BufferedPaintDC(self)

		# Initialize the wx.BufferedPaintDC, assigning a background
        # colour and a foreground colour (to draw the text)
		backColour = self.GetBackgroundColour()
		backBrush = wx.Brush(backColour, wx.SOLID)
		pdc.SetBackground(backBrush)
		pdc.Clear()

		try:
			dc = wx.GCDC(pdc)
		except:
			dc = pdc

		### to insure the correct redraw when window is scolling
		### http://markmail.org/thread/hytqkxhpdopwbbro#query:+page:1+mid:635dvk6ntxsky4my+state:results
		self.PrepareDC(dc)

		self.DoDrawing(dc)

	@Post_Undo
	def OnLock(self, event):
		"""
		"""
		for s in self.getSelectedShapes():
			if hasattr(s,'lock'):
				s.lock()

	@Post_Undo
	def OnUnLock(self, event):
		"""
		"""
		for s in self.getSelectedShapes():
			if hasattr(s,'unlock'):
				s.unlock()

	def OnRightDown(self, event):
		""" Mouse Right Down event manager.
		"""

		# if the timer used for the port number shortcut is active, we stop it.
		if self.timer.IsRunning():
			self.timer.Stop()

		# current shape
		s = self.getCurrentShape(event)

		# clic on canvas
		if self.isSelected(s):
			### call OnRightDown of selected object
			s.OnRightDown(event)
		else:
			menu = Menu.ShapeCanvasPopupMenu(self)

			### Show popup_menu
			self.PopupMenu(menu, event.GetPosition())

			### destroy menu local variable
			menu.Destroy()

		### Refresh canvas
		self.Refresh()

		### Focus on canvas
		#wx.CallAfter(self.SetFocus)

	def GetNodeLists(self, source, target):
		"""
		"""

		# list of node list for
		sourceINodeList = filter(lambda n: not isinstance(n, ResizeableNode) and isinstance(n, INode), self.nodes)
		sourceONodeList = filter(lambda n: not isinstance(n, ResizeableNode) and isinstance(n, ONode), self.nodes)

		# deselect and select target in order to get its list of node (because the node are generated dynamicly)
		self.deselect()
		self.select(target)

		nodesList=filter(lambda n: not isinstance(n, ResizeableNode), self.nodes)

		if isinstance(target,Block):
			if isinstance(source, oPort):
				sourceNodeList = sourceINodeList
				targetNodeList = filter(lambda n: not n in sourceONodeList and isinstance(n,ONode),nodesList)
			elif isinstance(source, iPort):
				sourceNodeList = sourceONodeList
				targetNodeList = filter(lambda n: not n in sourceINodeList and isinstance(n,INode),nodesList)
			else:
				sourceNodeList = sourceONodeList
				if not PORT_RESOLUTION:
					sourceNodeList += sourceINodeList
					targetNodeList = filter(lambda n: not n in sourceNodeList,nodesList)
				else:
					targetNodeList = filter(lambda n: not n in sourceNodeList and isinstance(n,INode),nodesList)

		elif isinstance(target,iPort):
			if isinstance(source, oPort):
				sourceNodeList = sourceINodeList
			elif isinstance(source, iPort):
				sourceNodeList = sourceONodeList
			else:
				sourceNodeList = sourceINodeList

			targetNodeList = filter(lambda n: not n in sourceONodeList and isinstance(n,ONode),nodesList)

		elif isinstance(target,oPort):
			if isinstance(source, oPort):
				sourceNodeList = sourceINodeList
			elif isinstance(source, iPort):
				sourceNodeList = sourceONodeList
			else:
				sourceNodeList = sourceONodeList
			targetNodeList = filter(lambda n: not n in sourceINodeList and isinstance(n,INode),nodesList)
		else:
			targetNodeList = []

		return (sourceNodeList, targetNodeList)

	def OnConnectTo(self, event):
		"""
		"""
		id = event.GetId()
		menu = event.GetEventObject()

		#source model from diagram
		source = self.getSelectedShapes()[0]

		# Model Name
		targetName = menu.GetLabelText(id)
		sourceName = source.label

		# get target model from its name
		for s in filter(lambda m: not isinstance(m,ConnectionShape), self.diagram.shapes):
			if s.label == targetName:
				target=s
				break

		### init source and taget node list
		self.sourceNodeList, self.targetNodeList = self.GetNodeLists(source, target)

		# Now we, if the nodes list are not empty, the connection can be proposed form ConnectDialog
		if self.sourceNodeList != [] and self.targetNodeList != []:
			if len(self.sourceNodeList) == 1 and len(self.targetNodeList) == 1:
				self.makeConnectionShape(self.sourceNodeList[0], self.targetNodeList[0])
			else:
				self.dlgConnection = ConnectDialog.ConnectDialog(wx.GetApp().GetTopWindow(), wx.ID_ANY, _("Connection Manager"), sourceName, self.sourceNodeList, targetName, self.targetNodeList)
				self.dlgConnection.Bind(wx.EVT_BUTTON, self.OnDisconnect, self.dlgConnection._button_disconnect)
				self.dlgConnection.Bind(wx.EVT_BUTTON, self.OnConnect, self.dlgConnection._button_connect)
				self.dlgConnection.Bind(wx.EVT_CLOSE, self.OnCloseConnectionDialog)
				self.dlgConnection.Show()

			self.DiagramModified()

	def OnDisconnect(self, event):
		""" Disconnect selected ports from connectDialog
		"""

		# dialog results
		sp,tp = self.dlgConnection._result

		### flag to inform if there are modifications
		modify_flag = False

		### if selected options are not 'All'
		if (    self.dlgConnection._combo_box_tn.StringSelection != _('All') \
				and self.dlgConnection._combo_box_sn.StringSelection != _('All')):
			for connectionShapes in filter(lambda s: isinstance(s, ConnectionShape), self.diagram.shapes):
				if (connectionShapes.getInput()[1] == sp) and (connectionShapes.getOutput()[1] == tp):
					self.RemoveShape(connectionShapes)
					modify_flag = True

		else:
			for connectionShapes in filter(lambda s: isinstance(s, ConnectionShape), self.diagram.shapes):
				self.RemoveShape(connectionShapes)
				modify_flag = True

		### shape has been modified
		if modify_flag:
			self.DiagramModified()
			self.deselect()
			self.Refresh()

	def OnConnect(self, event):
		"""     Connect selected ports from connectDialog
		"""

		# dialog results
		sp,tp = self.dlgConnection._result

		### if one of selected option is All
		if (    self.dlgConnection._combo_box_tn.StringSelection == _('All') \
				and self.dlgConnection._combo_box_sn.StringSelection != _('All')):
			sn = self.sourceNodeList[sp]
			for tn in self.targetNodeList:
				self.makeConnectionShape(sn, tn)
		### if one of selected option is All
		elif (  self.dlgConnection._combo_box_sn.StringSelection == _('All') \
				and self.dlgConnection._combo_box_tn.StringSelection != _('All')):
			tn = self.targetNodeList[tp]
			for sn in self.sourceNodeList:
				self.makeConnectionShape(sn, tn)
		### if both combo box selection are All, delete all of the connection from the top to the bottom
		elif (  self.dlgConnection._combo_box_tn.StringSelection == _('All') \
				and self.dlgConnection._combo_box_sn.StringSelection == _('All')) \
				and len(self.sourceNodeList)==len(self.targetNodeList):
			for sn,tn in map(lambda a,b: (a,b), self.sourceNodeList, self.targetNodeList):
				self.makeConnectionShape(sn,tn)
		### else make simple connection between sp and tp port number of source and target
		else:
			sn = self.sourceNodeList[sp]
			tn = self.targetNodeList[tp]
			self.makeConnectionShape(sn,tn)

		self.Refresh()

	@Post_Undo
	def makeConnectionShape(self, sourceNode, targetNode):
		""" Make new ConnectionShape from input number(sp) to output number (tp)
		"""

		# préparation et ajout dans le diagramme de la connection
		ci = ConnectionShape()
		self.diagram.shapes.insert(0, ci)

		# connection physique
		if isinstance(sourceNode, ONode):
			ci.setInput(sourceNode.item, sourceNode.index)
			ci.x[0], ci.y[0] = sourceNode.item.getPortXY('output', sourceNode.index)
			ci.x[1], ci.y[1] = targetNode.item.getPortXY('input', targetNode.index)
			ci.setOutput(targetNode.item, targetNode.index)

		else:
			ci.setInput(targetNode.item, targetNode.index)
			ci.x[1], ci.y[1] = sourceNode.item.getPortXY('output', sourceNode.index)
			ci.x[0], ci.y[0] = targetNode.item.getPortXY('input', targetNode.index)
			ci.setOutput(sourceNode.item, sourceNode.index)

		# selection de la nouvelle connection
		self.deselect()
		self.select(ci)

	def OnCloseConnectionDialog(self, event):
		"""
		"""
		# deselection de la dernier connection creer
		self.deselect()
		self.Refresh()
		# destruction du dialogue
		self.dlgConnection.Destroy()

	def OnMiddleDown(self, event):
		"""
		"""
		self.scroller.Start(event.GetPosition())

	def OnMiddleUp(self, event):
		"""
		"""
		self.scroller.Stop()

	def OnCopy(self, event):
		"""
		"""
		del clipboard[:]
		for m in self.select():
			clipboard.append(m)

		# main windows statusbar update
		printOnStatusBar(self.GetTopLevelParent().statusbar, {0:_('Copy'), 1:''})

	#def OnScroll(self, event):
		##"""
		##"""
		#event.Skip()

	def OnProperties(self, event):
		""" Properties sub menu has been clicked. Event is transmit to the model
		"""
		# pour passer la fenetre principale à OnProperties qui est deconnecte de l'application du faite de popup
		event.SetEventObject(self)
		for s in self.select():
			s.OnProperties(event)

	def OnLog(self, event):
		""" Log sub menu has been clicked. Event is transmit to the model
		"""
		event.SetClientData(self.GetTopLevelParent())
		for s in self.select():
			s.OnLog(event)

	def OnEditor(self, event):
		""" Edition sub menu has been clicked. Event is transmit to the model
		"""

		event.SetClientData(self.GetTopLevelParent())
		for s in self.select():
			s.OnEditor(event)

	@staticmethod
	def StartWizard(parent):
		""" New model menu has been pressed. Wizard is instanciate.
		"""

		### arguments of ModelGeneratorWizard when right clic appears in canvas
		kargs = {'title' : _('DEVSimPy Model Generator'),
					'parent' : parent,
					'img_filename' : os.path.join('bitmaps', DEVSIMPY_PNG)}

		### right clic appears in a library
		if not isinstance(parent, ShapeCanvas):
			### Get path of the selected lib in order to change the last step of wizard
			sdp = parent.GetItemPyData(parent.GetFocusedItem())
			kargs['specific_domain_path']=sdp

		gmwiz = WizardGUI.ModelGeneratorWizard(**kargs)
		gmwiz.run()

		### just for Mac
		if not gmwiz.canceled_flag:
			return gmwiz
		else:
			return None

	def OnNewModel(self, event):
		""" New model menu has been pressed. Wizard is instanciate.
		"""

		###mouse postions
		xwindow, ywindow = wx.GetMousePosition()
		x,y = self.ScreenToClientXY(xwindow, ywindow)

		obj = event.GetEventObject()

		### if right clic on canvas
		if isinstance(obj, Menu.ShapeCanvasPopupMenu):
			parent = self
		else:
			parent = wx.GetApp().GetTopWindow().GetControlNotebook().GetTree()

		gmwiz = ShapeCanvas.StartWizard(parent)

		# if wizard is finished witout closing
		if  gmwiz :
			m = Components.BlockFactory.CreateBlock(      canvas = self,
												x = x,
												y = y,
												label = gmwiz.label,
												id = gmwiz.id,
												inputs = gmwiz.inputs,
												outputs = gmwiz.outputs,
												python_file = gmwiz.python_path,
												model_file = gmwiz.model_path,
												specific_behavior = gmwiz.specific_behavior)
			if m:

				### save visual model
				if gmwiz.overwrite_flag and isinstance(m, Block):
					if m.SaveFile(gmwiz.model_path):
						m.last_name_saved = gmwiz.model_path
					else:
						dlg = wx.MessageDialog(self, \
											_('Error saving file %s\n')%os.path.basename(gmwiz.model_path), \
											gmwiz.label, \
											wx.OK | wx.ICON_ERROR)
						dlg.ShowModal()

				# Adding graphical model to diagram
				self.AddShape(m)

				sys.stdout.write(_("Adding DEVSimPy model: \n").encode('utf-8'))
				sys.stdout.write(repr(m))

				# try to update the library tree on left panel
				#tree = wx.GetApp().GetTopWindow().tree
				#tree.UpdateDomain(str(os.path.dirname(gmwiz.model_path)))

				# focus
				#wx.CallAfter(self.SetFocus)

			# Cleanup
			gmwiz.Destroy()

	@BuzyCursorNotification
	def OnPaste(self, event):
		""" Paste menu has been clicked.
		"""

		D = {}  # correspondance between the new and the paste model
		L = []  # list of original connectionShape components

		for m in clipboard:
			if isinstance(m, ConnectionShape):
				L.append(copy.copy(m))
			else:
				# make new shape
				newShape = m.Copy()
				# store correspondance (for coupling)
				D[m]= newShape
				# move new modele
				newShape.x[0] += 35
				newShape.x[1] += 35
				newShape.y[0] += 35
				newShape.y[1] += 35
				### adding model
				self.AddShape(newShape)

		### adding connectionShape
		for cs in L:
			cs.input = (D[cs.input[0]],cs.input[1])
			cs.output = (D[cs.output[0]],cs.output[1])
			self.AddShape(cs)

		# specify the operation in status bar
		printOnStatusBar(self.GetTopLevelParent().statusbar, {0:_('Paste'), 1:''})

	def OnCut(self, event):
		""" Cut menu has been clicked. Copy and delete event.
		"""

		self.OnCopy(event)
		self.OnDelete(event)

	def OnDelete(self, event):
		"""     Delete menu has been clicked. Delete all selected shape.
		"""

		if len(self.select()) > 1:
			msg = _("Do you really want to delete all selected models?")
 			dlg = wx.MessageDialog(self, msg,
			 						_("Delete Manager"),
									wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

			if dlg.ShowModal() not in [wx.ID_NO, wx.ID_CANCEL]:
				for s in self.select():
					self.diagram.DeleteShape(s)
			dlg.Destroy()

		else:
			for s in self.select():
	   			name = _("Connexion") if isinstance(s, ConnectionShape) else s.label
				msg = _("Do you really want to delete %s model?")%(name)
	 			dlg = wx.MessageDialog(self, msg,
				 						_("Delete Manager"),
										wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

				if dlg.ShowModal() not in [wx.ID_NO, wx.ID_CANCEL]:
					self.diagram.DeleteShape(s)
				dlg.Destroy()

		self.DiagramModified()
		self.deselect()

	def DiagramReplace(self, d):

		self.diagram = d

		self.DiagramModified()
		self.deselect()
		self.Refresh()

	def OnRightUp(self,event):
		"""
		"""
		try:
			self.getCurrentShape(event).OnRightUp(event)
		except AttributeError:
			pass

	def OnRightDClick(self,event):
		"""
		"""
		try:
			self.getCurrentShape(event).OnRightDClick(event)
		except AttributeError:
			pass

	def OnLeftDClick(self,event):
		"""
		"""

		model = self.getCurrentShape(event)
		if model:
			if model.OnLeftDClick:
				model.OnLeftDClick(event)
			else:
				wx.MessageBox(_("An error is occured during plugins importation.\nCheck plugins module."))

	def Undo(self):
		"""
		"""

		mainW = self.GetTopLevelParent()

		### dump solution
		### if parent is not none, the dumps dont work because parent is copy of a class
		try:
			t = cPickle.loads(self.stockUndo[-1])

			### we add new undo of diagram has been modified or one of the shape in diagram sotried in stockUndo has been modified.
			if any(objA.__dict__ != objB.__dict__ for objA in self.diagram.GetShapeList() for objB in t.GetShapeList()):
				self.stockUndo.append(cPickle.dumps(obj=self.diagram, protocol=0))
		except IndexError:
			### this is the first call of Undo and StockUndo is emplty
			self.stockUndo.append(cPickle.dumps(obj=self.diagram, protocol=0))
		except TypeError, info:
			sys.stdout.write(_("Error trying to undo (TypeError): %s \n"%info))
		except Exception, info:
			sys.stdout.write(_("Error trying to undo: %s \n"%info))
		finally:

			### just for init (white diagram)
			if self.diagram.GetBlockCount()>=1:
				### toolBar
				tb = mainW.FindWindowByName('tb')
				tb.EnableTool(wx.ID_UNDO, True)

				self.diagram.parent = self
				### note that the diagram is modified
				self.diagram.modify = True
				self.DiagramModified()

	def OnLeftDown(self,event):
		""" Left Down mouse bouton has been invoked in the canvas instance.
		"""

		if self.timer.IsRunning():
			self.timer.Stop()

		### get current shape
		item = self.getCurrentShape(event)

		### clicked on empty space deselect all
		if item is None:
			self.deselect()

			### recover focus
			if wx.Window.FindFocus() != self:
				self.SetFocus()

			## Left mouse button down, change cursor to
			## something else to denote event capture
			if not self.HasCapture():
				self.CaptureMouse()
			self.overlay = wx.Overlay()
			self.selectionStart = event.Position

		else:

			### if item is not selected, then we select it without the other
			if item not in self.getSelectedShapes():

				item.OnLeftDown(event) # send leftdown event to current shape
				if isinstance(item, Selectable) and not event.ShiftDown():
					self.deselect()

				self.select(item)

			### else each other are considered
			else:

				for s in self.getSelectedShapes():
					s.OnLeftDown(event) # send leftdown event to current shape

		### Update the nb1 panel properties only for Block and Port (call update in ControlNotebook)
		if isinstance(item, Attributable):
			self.__state['model'] = item
			self.__state['canvas'] = self
			self.notify()

		self.Refresh()

	###
	@Post_Undo
	def OnLeftUp(self, event):
		"""
		"""
		shape = self.getCurrentShape(event)

		self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

		### clic sur un block
		if shape:

			shape.OnLeftUp(event)
			shape.leftUp(self.select())

			remove = True
			### empty connection manager
			for item in filter(lambda s: isinstance(s, ConnectionShape), self.select()):
				### restore solid connection
				if len(item.pen)>2:
					item.pen[2]= wx.SOLID

				if None in (item.output, item.input):

					### gestion des ajouts de connections automatiques
					for ss in filter(lambda a: isinstance(a, Block), self.diagram.GetShapeList()):
						try:
							### si le shape cible (ss) n'est pas le shape que l'on est en train de traiter (pour eviter les auto-connexions)
							if (shape.item.output is not None and ss not in shape.item.output) or \
							(shape.item.input is not None and ss not in shape.item.input):
								x = ss.x[0]*self.scalex
								y = ss.y[0]*self.scaley
								w = (ss.x[1]-ss.x[0])*self.scalex
								h = (ss.y[1]-ss.y[0])*self.scaley
								recS = wx.Rect(x,y,w,h)

								### extremité de la connectionShape
								extrem = event.GetPosition()

								### si l'extremité est dans le shape cible (ss)
								if (ss.x[0] <= extrem[0] <= ss.x[1]) and (ss.y[0] <= extrem[1] <= ss.y[1]):

									### new link request
									dlg = wx.TextEntryDialog(self, _('Choose the port number.\nIf doesn\'t exist, we create it.'),_('Coupling Manager'))
									if item.input is None:
										dlg.SetValue(str(ss.output))
										if dlg.ShowModal() == wx.ID_OK:
											try:
												val=int(dlg.GetValue())
											### is not digit
											except ValueError:
												pass
											else:
												if val >= ss.output:
													nn = ss.output
													ss.output+=1
												else:
													nn = val
												item.input = (ss, nn)
												### dont avoid the link
												remove = False
									else:
										dlg.SetValue(str(ss.input))
										if dlg.ShowModal() == wx.ID_OK:
											try:
												val=int(dlg.GetValue())
											### is not digit
											except ValueError:
												pass
											else:
												if val >= ss.input:
													nn = ss.input
													ss.input+=1
												else:
													nn = val
												item.output = (ss, nn)
												### dont avoid the link
												remove = False

						except AttributeError:
							### TODO: I dont now why !!!
							pass

					if remove:
						self.diagram.DeleteShape(item)
						self.deselect()
				else:
					### transformation de la connection en zigzag
					pass

		### click on canvas
		else:

			### Rubber Band with overlay
			## User released left button, change cursor back
			if self.HasCapture():
				self.ReleaseMouse()
				self.permRect = wx.RectPP(self.selectionStart, event.Position)
				self.selectionStart = None
				self.overlay.Reset()

				self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

				## gestion des shapes qui sont dans le rectangle permRect
				for s in self.diagram.GetShapeList():
					x = s.x[0]*self.scalex
					y = s.y[0]*self.scaley
					w = (s.x[1]-s.x[0])*self.scalex
					h = (s.y[1]-s.y[0])*self.scaley
					recS = wx.Rect(x,y,w,h)

					# si les deux rectangles se chevauche
					try:
						if self.permRect.ContainsRect(recS):
							self.select(s)
					except AttributeError:
						raise(_("use >= wx-2.8-gtk-unicode library"))
								#clear out any existing drawing

		self.Refresh()

	def OnTimer(self, event):
		"""
		"""
		if self.f:
			self.f.Show()

	def OnMouseEnter(self, event):
		"""
		"""
		self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

	def OnMouseLeave(self, event):
		"""
		"""
		pass
		#self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

	def DiagramModified(self):
		""" Modification printing in statusbar and modify value manager.

			This method manage the propagation of modification
			from window where modifications are performed to DEVSimPy main window.

		"""

		if self.diagram.modify:
			### window where modification is performed
			win = self.GetTopLevelParent()

			if isinstance(win, DetachedFrame):
				### main window
				mainW = wx.GetApp().GetTopWindow()

				if not isinstance(mainW, DetachedFrame):
					nb2 = mainW.GetDiagramNotebook()
					canvas = nb2.GetPage(nb2.GetSelection())
					diagram = canvas.GetDiagram()
					### modifying propagation
					diagram.modify = True
					### update general shapes
					canvas.UpdateShapes()

					label = nb2.GetPageText(nb2.GetSelection())

					### modified windows dictionary
					D = {win.GetTitle(): win, label: mainW}
				else:
					D={}
			else:
				nb2 = win.GetDiagramNotebook()
				canvas = nb2.GetPage(nb2.GetSelection())
				diagram = canvas.GetDiagram()
				diagram.modify = True
				label = nb2.GetPageText(nb2.GetSelection())

				D = {label : win}

			#nb.SetPageText(nb.GetSelection(), "*%s"%label.replace('*',''))

			### statusbar printing
			for string,win in D.items():
				printOnStatusBar(win.statusbar, {0:"%s %s"%(string ,_("modified")), 1:os.path.basename(diagram.last_name_saved), 2:''})

			win.FindWindowByName('tb').EnableTool(Menu.ID_SAVE, self.diagram.modify)
	###
	def OnMotion(self, event):
		""" Motion manager.
		"""

		if event.Dragging() and event.LeftIsDown():

			self.diagram.modify = False

			point = self.getEventCoordinates(event)
			x = point[0] - self.currentPoint[0]
			y = point[1] - self.currentPoint[1]

			for s in self.getSelectedShapes():
				s.move(x,y)

				### change cursor when resizing model
				if isinstance(s, ResizeableNode):
					self.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))

				### change cursor when connectionShape hit a node
				elif isinstance(s, ConnectionShape):
					### dot trace to prepare connection
					if len(s.pen)>2:
						s.pen[2]= wx.DOT

					self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))

					for node in filter(lambda n: isinstance(n, ConnectableNode), self.nodes):
						if node.HitTest(point[0], point[1]):
							self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
						#else:
							#self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))

					## list of shape connected to the connectionShape (for exclude these of the catching engine)
					#L = s.input or ()
					#L += s.output or ()

					#### try to catch connectionShape with block
					#for ss in filter(lambda n: (isinstance(n, Block) or isinstance(n, Port) ) and n not in L, self.diagram.shapes):
						#touch = False
						#for line in range(len(s.x)-1):
							#try:
								#### get a and b coeff for linear equation
								#a = (s.y[line]-s.y[line+1])/(s.x[line]-s.x[line+1])
								#b = s.y[line] -a*s.x[line]
								#### X and Y points of linear equation
								#X = range(int(s.x[line]), int(s.x[line+1]))
								#Y = map(lambda x: a*x+b,X)
								## if one point of the connectionShape hit the shape, we chage its geometry
								#for px,py in zip(X, Y):
									#if ss.HitTest(px,py):
										#touch=True
							#except ZeroDivisionError:
								#pass
						## if ss is crossed, we add it on the containerShape touch_list
						#if touch:
							##print ss
							#if ss not in s.touch_list:
								#s.touch_list.append(ss)
							#print "touch %s"%ss.label
				else:
					self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
					pass

				self.diagram.modify = True

			self.currentPoint = point

			if self.getSelectedShapes() == []:
				# User is dragging the mouse, check if
				# left button is down
				if self.HasCapture():
					self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
					dc = wx.ClientDC(self)
					odc = wx.DCOverlay(self.overlay, dc)
					odc.Clear()
					ctx = wx.GraphicsContext_Create(dc)
					ctx.SetPen(wx.GREY_PEN)
					ctx.SetBrush(wx.Brush(wx.Colour(229,229,229,80)))
					ctx.DrawRectangle(*wx.RectPP(self.selectionStart, event.Position))
					del odc
				else:
					self.Refresh()
			else:
				### refresh all canvas with Flicker effect corrected in OnPaint and OnEraseBackground
				self.Refresh()

		# gestion du pop up pour la modification du nombre de port
		else:

			# mouse postions
			xwindow, ywindow = wx.GetMousePosition()
			xm,ym = self.ScreenToClientXY(xwindow, ywindow)

			mainW = self.GetTopLevelParent()

			flag = True
			### find if window exists on the top of model, then inactive the QuickAttributeEditor
			for win in filter(lambda w: w.IsTopLevel(), mainW.GetChildren()):
				if win.IsActive():
					flag = False

			if self.f:
				self.f.Close()
				self.f = None

			for s in filter(lambda m: isinstance(m, Block), self.diagram.GetShapeList()):
				x = s.x[0]*self.scalex
				y = s.y[0]*self.scaley
				w = (s.x[1]-s.x[0])*self.scalex
				h = (s.y[1]-s.y[0])*self.scaley

				# if mousse over hight the shape
				try:

					if (x<=xm and xm < x+w) and (y<=ym and ym < y+h):
						if self.isSelected(s) and flag:
							self.f = QuickAttributeEditor(self, wx.ID_ANY, s)
							self.timer.Start(1200)
							break
						else:
							if self.timer.IsRunning():
								self.timer.Stop()

				except AttributeError:
					raise(_("use >= wx-2.8-gtk-unicode library"))

		self.DiagramModified()

	def SetDiagram(self, diagram):
		""" Setter for diagram attribute.
		"""
		self.diagram = diagram

	def GetDiagram(self):
		""" Return Diagram instance.
		"""
		return self.diagram

	def getCurrentShape(self, event):
		""" Return the selected current shape.
		"""
		# get coordinate of click in our coordinate system
		point = self.getEventCoordinates(event)
		self.currentPoint = point

		# Look to see if an item is selected
		for item in self.nodes + self.diagram.shapes:
			if item.HitTest(point[0], point[1]):
				return item

		return None

	def GetXY(self, m, x, y):
		""" Give x and y of model m into canvas.
		"""
		dx = (m.x[1]-m.x[0])
		dy = (m.y[1]-m.y[0])
		ux,uy = self.getScalledCoordinates(x,y)
		#ux, uy = canvas.CalcUnscrolledPosition(x-dx, y-dy)

		return (ux-dx,uy-dy)

	def getScalledCoordinates(self, x, y):
		""" Return coordiante depending on the zoom.
		"""
		originX, originY = self.GetViewStart()
		unitX, unitY = self.GetScrollPixelsPerUnit()
		return ((x + (originX * unitX))/ self.scalex, (y + (originY * unitY))/ self.scaley)

	def getEventCoordinates(self, event):
		""" Return the coordinates from event.
		"""
		return self.getScalledCoordinates(event.GetX(),event.GetY())

	def getSelectedShapes(self):
		""" Retrun the list of selected object on the canvas (Connectable nodes are excluded)
		"""
		return self.selectedShapes

	def isSelected(self, s):
		""" Check of shape s is selected.
			If s is a ConnectableNode object, it implies that is visible and then selected !
		"""
		return (s) and (s in self.selectedShapes) or isinstance(s, ConnectableNode)

	def getName(self):
		""" Return the name
		"""
		return self.name

	def deselect(self, item=None):
		""" Deselect all shapes
		"""

		if item is None:
			for s in self.selectedShapes:
				s.OnDeselect(None)
			del self.selectedShapes[:]
			del self.nodes[:]
		else:
			self.nodes = [ n for n in self.nodes if n.item != item]
			self.selectedShapes = [ n for n in self.selectedShapes if n != item]
			item.OnDeselect(None)

	### selectionne un shape
	def select(self, item=None):
		""" Select the models in param item
		"""

		if item is None:
			return self.selectedShapes

		if isinstance(item, Node):
			del self.selectedShapes[:]
			self.selectedShapes.append(item) # items here is a single node
			return

		if not self.isSelected(item):
			self.selectedShapes.append(item)
			item.OnSelect(None)
			if isinstance(item, Connectable):
				self.nodes.extend([INode(item, n, self) for n in xrange(item.input)])
				self.nodes.extend([ONode(item, n, self) for n in xrange(item.output)])
			if isinstance(item, Resizeable):
				self.nodes.extend([ResizeableNode(item, n, self) for n in xrange(len(item.x))])

	###
	def UpdateShapes(self, L=None):
		""" Method that update the graphic of the models composing the parameter list.
		"""

		# update all models in canvas
		if L is None:
			L = self.diagram.shapes

		# select all models in selectedList and refresh canvas
		for m in filter(self.isSelected, L):
			self.deselect(m)
			self.select(m)

		self.Refresh()

	### selection sur le canvas les ONodes car c'est le seul moyen d'y accéder pour effectuer l'appartenance avec les modèles
	def showOutputs(self, item=None):
		""" Populate nodes list with output ports.
		"""
		if item:
			self.nodes.extend([ONode(item, n, self) for n in xrange(item.output)])
		else:
			for s in filter(lambda a: isinstance(a, Connectable), self.diagram.shapes):
				self.nodes.extend([ONode(s, n, self) for n in xrange(s.output)])

	### selection sur le canvas les INodes car c'est le seul moyen d'y accéder pour effectuer l'appartenance avec les modèles
	def showInputs(self,item=None):
		""" Populate nodes list with output ports.
		"""
		if item:
			self.nodes.extend([INode(item, n, self) for n in xrange(item.input)])
		else:
			for s in filter(lambda a: isinstance(a, Connectable), self.diagram.shapes):
				self.nodes.extend([INode(s, n, self) for n in xrange(s.input)])

	def GetState(self):
		return self.__state

#-----------------------------------------------------------
class LinesShape(Shape):
	"""
	"""

	def __init__(self, line):
		""" Constructor.
		"""
		Shape.__init__(self)

		self.fill = ['#d91e1e']
		self.x = array.array('d', line.x)
		self.y = array.array('d', line.y)

	def draw(self, dc):
		""" Drawing line.
		"""
		Shape.draw(self, dc)

		L = map(lambda a,b: (a,b), self.x, self.y)

		### update L depending of the connector type
		if ShapeCanvas.CONNECTOR_TYPE == 'linear':
			### line width
			w = self.x[1] - self.x[0]
			### left moving
			if w > 0:
				### output port
				if self.input:
					L.insert(1, (self.x[0]+w/10, self.y[0]))
					L.insert(2, (self.x[1]-w/10, self.y[1]))
				else:
					L.insert(1, (self.x[0]+w/10, self.y[0]))
					L.insert(2, (self.x[1]-w/10, self.y[1]))
			### right moving
			else:
				### output port
				if self.input:
					L.insert(1, (self.x[0]-w/10, self.y[0]))
					L.insert(2, (self.x[1]-w/10, self.y[1]))
				else:
					L.insert(1, (self.x[0]+w/10, self.y[0]))
					L.insert(2, (self.x[1]+w/10, self.y[1]))

		elif ShapeCanvas.CONNECTOR_TYPE == 'square':
			### line width
			w = self.x[1] - self.x[0]
			L.insert(1,(self.x[0]+w/2, self.y[0]))
			L.insert(2,(self.x[0]+w/2, self.y[1]))

		else:
			pass

		dc.DrawLines(L)

		### pour le rectangle en fin de connexion
		dc.DrawRectanglePointSize(wx.Point(self.x[-1]-10/2, self.y[-1]-10/2), wx.Size(10, 10))
		#dc.DrawPolygon((	wx.Point(self.x[-1]-10, self.y[-1]-10),
		#					wx.Point(self.x[-1]-10, self.y[-1]+10),
		#					wx.Point(self.x[-1], self.y[-1]),
		#					wx.Point(self.x[-1]-10, self.y[-1]-10)))

	def HitTest(self, x, y):
		"""
		"""

		if x < min(self.x)-3:return False
		if x > max(self.x)+3:return False
		if y < min(self.y)-3:return False
		if y > max(self.y)+3:return False

		ind = 0
		try:
			while 1:
				x1 = self.x[ind]
				y1 = self.y[ind]
				x2 = self.x[ind+1]
				y2 = self.y[ind+1]

				top= (x-x1) *(x2 - x1) + (y-y1)*(y2-y1)
				distsqr = pow(x1-x2, 2) + pow(y1-y2, 2)
				u = float(top)/float(distsqr)

				newx = x1 + u*(x2-x1)
				newy = y1 + u*(y2-y1)

				dist = pow(pow(newx-x, 2) + pow(newy-y, 2),.5)

				if dist < 7:
					return True
				ind = ind + 1

		except:
			pass

		return False

	def OnLeftDClick(self, event):
		""" Left click has been invoked.
		"""

		### canvas containing LinesShape
		canvas = event.GetEventObject()

		### coordinates
		x,y = event.GetPositionTuple()
		### add point at the position according to the possible zoom (use of getScalledCoordinates)
		self.AddPoint(canvas.getScalledCoordinates(x,y))

	def HasPoint(self, point):
		""" Point is included in line ?
		"""

		x,y = point
		return (x in self.x) and (y in self.y)

	def AddPoint(self, point = (0,0)):
		""" Add point under LineShape.
		"""
		x,y = point

		# insertion sur les morceaux de droites d'affines
		for i in xrange(len(self.x)-1):
			x1 = self.x[i]
			x2 = self.x[i+1]

			y1 = self.y[i]
			y2 = self.y[i+1]

			if (x1<=x<=x2 and y1<=y<=y2) or ((x1<=x<=x2 and y2<y<y1) or (x2<=x<=x1 and y1<=y<=y2) or (x2<=x<=x1 and y2<=y<=y1)):
				self.x.insert(i+1, x)
				self.y.insert(i+1, y)

				#### cassure des locks
				self.unlock()
				break

# Mixins------------------------------------------------------------------------
###---------------------------------------------------------------------------------------------------------
# NOTE: Testable << object :: Testable mixin is needed to manage tests files and tests executions. It add the OnTestEditor event for the tests files edition
class Testable(object):

	# NOTE: Testable :: OnTestEditor 		=> new event for AMD model. Open tests files in editor
	def OnTestEditor(self, event):
		"""
		"""

		L = self.GetTestFile()

		### create Editor with BDD files in tab
		if L != []:

			#model_path = os.path.dirname(self.python_path)

			# TODO: Testable :: OnTestEditor => Fix Editor importation
			import Editor

			#mainW = wx.GetApp().GetTopWindow()
			### Editor instanciation and configuration---------------------
			editorFrame = Editor.GetEditor(
					None,
					wx.ID_ANY,
					'Features',
					file_type="test"
			)

			for i,s in enumerate(map(lambda l: os.path.join(self.model_path, l), L)):
				editorFrame.AddEditPage(L[i], s)

			editorFrame.Show()
			### -----------------------------------------------------------

	def GetTestFile(self):
		""" Get Test file only for AMD model
		"""

		# If selected model is AMD
		if self.isAMD():

			# Create tests files is doesn't exist
			if not ZipManager.Zip.HasTests(self.model_path):
				self.CreateTestsFiles()

			### list of BDD files
			L = ZipManager.Zip.GetTests(self.model_path)

			return L

		return []

	# NOTE: Testable :: isAMD 				=> Test if the model is an AMD and if it's well-formed
	def isAMD(self):
		return zipfile.is_zipfile(os.path.dirname(self.python_path))

	# NOTE: Testable :: CreateTestsFiles	=> AMD tests files creation
	def CreateTestsFiles(self):
		devsPath = os.path.dirname(self.python_path)
		name = os.path.splitext(os.path.basename(self.python_path))[0]
		zf = ZipManager.Zip(devsPath)

		feat, steps, env = self.CreateFeature(), self.CreateSteps(), Testable.CreateEnv()

		zf.Update([os.path.join('BDD', feat), os.path.join('BDD', steps), os.path.join('BDD', env)])

		if os.path.exists(feat): os.remove(feat)
		if os.path.exists(steps): os.remove(steps)
		if os.path.exists(env): os.remove(env)

		#if not zf.HasTests():

			#files = zf.GetTests()
			#if not '%s.feature'%name in files:
				#feat = self.CreateFeature()
				#zf.Update([os.path.join('BDD', feat)])
				#os.remove(feat)
			#if not 'steps.py' in files:
				#steps = self.CreateSteps()
				#zf.Update([os.path.join('BDD',steps)])
				#os.remove(steps)
			#if not 'environment.py' in files:
				#env = self.CreateEnv()
				#zf.Update([os.path.join('BDD',env)])
				#os.remove(env)

	# NOTE: Testable :: CreateFeature		=> Feature file creation
	def CreateFeature(self):
		name = os.path.splitext(os.path.basename(self.python_path))[0]
		feature = "%s.feature"%name
		with open(feature, 'w+') as feat:
			feat.write("# -*- coding: utf-8 -*-\n")

		return feature

	# NOTE: Testable :: CreateSteps		=> Steps file creation
	def CreateSteps(self):
		steps = "steps.py"
		with open(steps, 'w+') as step:
			step.write("# -*- coding: utf-8 -*-\n")

		return steps

	# NOTE: Testable :: CreateEnv		=> Environment file creation
	@staticmethod
	def CreateEnv(path=None):
		if path:
			environment = os.path.join(path, 'environment.py')
		else:
			environment = "environment.py"
		with open(environment, 'w+') as env:
			env.write("# -*- coding: utf-8 -*-\n")

		return environment

	# NOTE: Testable :: GetTempTests		=> Create tests on temporary folder for execution
	def GetTempTests(self, global_env=None):
		if not global_env: global_env = False

		### Useful vars definition-----------------------------------------------------------------
		model_path = os.path.dirname(self.python_path)
		basename = os.path.basename(self.python_path)
		name = os.path.splitext(basename)[0]
		tests_files = ZipManager.Zip.GetTests(model_path)
		### ---------------------------------------------------------------------------------------

		### Folder hierarchy construction----------------------------------------------------------
		feat_dir  = os.path.join(gettempdir(), "features")
		steps_dir = os.path.join(feat_dir, "steps")
		if not os.path.exists(feat_dir):
			os.mkdir(feat_dir)
		if not os.path.exists(steps_dir):
			os.mkdir(steps_dir)
		### ---------------------------------------------------------------------------------------

		### AMD unzip------------------------------------------------------------------------------
		amd_dir = os.path.join(gettempdir(), "AtomicDEVS")
		if not os.path.exists(amd_dir):
			os.mkdir(amd_dir)
		### ---------------------------------------------------------------------------------------

		### Tests code retriever-------------------------------------------------------------------
		importer = zipfile.ZipFile(model_path)

		feat_name = filter(lambda t: t.endswith('.feature'), tests_files)[0]
		featInfo = importer.getinfo(feat_name)
		feat_code = importer.read(featInfo)

		steps_name = filter(lambda t: t.endswith('steps.py'), tests_files)[0]
		stepsInfo = importer.getinfo(steps_name)
		steps_code = importer.read(stepsInfo)

		if not global_env:
			environment_name = filter(lambda t: t.endswith('environment.py'), tests_files)[0]
			envInfo = importer.getinfo(environment_name)
			env_code = importer.read(envInfo)
		else:
			environment_name = os.path.join(gettempdir(), 'environment.py')
			with open(environment_name, 'r+') as global_env_code:
				env_code = global_env_code.read()

		importer.close()
		### ---------------------------------------------------------------------------------------

		### AMD code retriever---------------------------------------------------------------------
		importer = zipfile.ZipFile(model_path)

		# amd_name = filter(lambda t: t.endswith('%s.py'%name), importer.namelist())[0]
		amd_name = ZipManager.getPythonModelFileName(model_path)
		amd_info = importer.getinfo(amd_name)
		amd_code = importer.read(amd_info)

		### ---------------------------------------------------------------------------------------

		### Tests files creation in temporary directory--------------------------------------------
		tempFeature = os.path.join(feat_dir, "%s.feature"%name)
		tempEnv = os.path.join(feat_dir, "environment.py")
		tempSteps = os.path.join(steps_dir, "%s_steps.py"%name)

		tempAMD = os.path.join(amd_dir, amd_name)

		with open(tempFeature, 'w+') as feat:
			feat.write(feat_code)
		with open(tempSteps, 'w+') as steps:
			steps.write(steps_code)
		with open(tempEnv, 'w+') as env:
			env.write(env_code)

		with open(tempAMD, 'w+') as AMD:
			AMD.write(amd_code)
		### ---------------------------------------------------------------------------------------

		return tempFeature, tempSteps, tempEnv

	# NOTE: Testable :: RemoveTempTests		=> Remove tests on temporary folder
	@staticmethod
	def RemoveTempTests():
		feat_dir = os.path.join(gettempdir(), 'features')
		if os.path.exists(feat_dir):
			for root, dirs, files in os.walk(feat_dir, topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
        		for name in dirs:
    				os.rmdir(os.path.join(root, name))

			os.rmdir(feat_dir)

		amd_dir = os.path.join(gettempdir(), 'AtomicDEVS')
		if os.path.exists(amd_dir):
			for root, dirs, files in os.walk(amd_dir, topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
        		for name in dirs:
    				os.rmdir(os.path.join(root, name))

			os.rmdir(amd_dir)

#---------------------------------------------------------
class ConnectionShape(LinesShape, Resizeable, Selectable, Structurable):
	""" ConnectionShape class
	"""


	def __init__(self):
		""" Constructor
		"""
		LinesShape.__init__(self, LineShape(0,0,1,1))
		Resizeable.__init__(self)
		Structurable.__init__(self)

		#Convertible.__init__(self, 'direct')

		self.input = None
		self.output = None
		self.touch_list = []
		self.lock_flag = False                  # move lock

	def __setstate__(self, state):
		""" Restore state from the unpickled state values.
		"""


		####################################" Just for old model
		if 'touch_list' not in state: state['touch_list'] = []
		if 'font' not in state: state['font'] = [FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, u'Arial']
		##############################################

		self.__dict__.update(state)

	def setInput(self, item, index):
		self.input = (item, index)

	def setOutput(self, item, index):
		self.output = (item, index)

	def getInput(self):
		return self.input

	def getOutput(self):
		return self.output

	def draw(self, dc):

		if self.input:
			self.x[0], self.y[0] = self.input[0].getPortXY('output', self.input[1])

		if self.output:
			self.x[-1],self.y[-1] = self.output[0].getPortXY('input', self.output[1])

		LinesShape.draw(self,dc)

	def lock(self):
		"""
		"""

		if self.input and self.output:
			host1 = self.input[0]
			host2 = self.output[0]

			try: host1.lock()
			except: pass

			try: host2.lock()
			except: pass

	def unlock(self):
		"""
		"""

		if self.input and self.output:
			host1 = self.input[0]
			host2 = self.output[0]

			try: host1.unlock()
			except: pass

			try: host2.unlock()
			except: pass

	def OnLeftDClick(self, event):
		""" Left Double click has been invoked.
		"""
		### redirect to LinesShape handler (default)
		LinesShape.OnLeftDClick(self, event)

	###
	def OnRightDown(self, event):
		""" Right down event has been invoked.
		"""
		menu = Menu.ShapePopupMenu(self, event)
		### Show popup_menu
		canvas = event.GetEventObject()
		canvas.PopupMenu(menu, event.GetPosition())
		### destroy menu local variable
		menu.Destroy()

	def __del__(self):
		pass

#Basic Graphical Components-----------------------------------------------------
class Block(RoundedRectangleShape, Connectable, Resizeable, Selectable, Attributable, Rotatable, Plugable, Observer, Testable, Savable):
	""" Generic Block class.
	"""

	def __init__(self, label = 'Block', nb_inputs = 1, nb_outputs = 1):
		""" Constructor
		"""

		RoundedRectangleShape.__init__(self)
		Resizeable.__init__(self)
		Connectable.__init__(self, nb_inputs, nb_outputs)
		Attributable.__init__(self)
		Selectable.__init__(self)
		Rotatable.__init__(self)

		self.AddAttributes(Attributable.GRAPHICAL_ATTR)
		self.label = label
		self.label_pos = 'center'
		self.image_path = ""
		self.id = 0
		self.nb_copy = 0        # nombre de fois que le bloc est copié (pour le label des blocks copiés
		self.last_name_saved = ""
		self.lock_flag = False                  # move lock
		self.bad_filename_path_flag = False

	###
	def draw(self, dc):
		"""
		"""

		### Draw rectangle shape
		RoundedRectangleShape.draw(self, dc)

		### Prepare label drawing
		w,h =  dc.GetTextExtent(self.label)
		mx = int((self.x[0] + self.x[1]-w)/2)

		if self.label_pos == 'bottom':
			### bottom
			my = int(self.y[1])
		elif self.label_pos == 'top':
			### top
			my = int(self.y[0]-h)
		else:
			### center
			my = int((self.y[0] + self.y[1]-h)/2)

		### with and height of rectangle
		self.w = self.x[1]- self.x[0]
		self.h = self.y[1]- self.y[0]

		### Draw background picture
		if os.path.isabs(self.image_path):
			dir_name = os.path.dirname(self.image_path)

			if zipfile.is_zipfile(dir_name):
				image_name = os.path.basename(self.image_path)
				image_path = os.path.join(gettempdir(), image_name)
				sourceZip = zipfile.ZipFile(dir_name, 'r')
				sourceZip.extract(image_name, gettempdir())
				sourceZip.close()
			else:
				image_path = self.image_path

			if os.path.isabs(image_path):
				img = wx.Image(image_path).Scale(self.w, self.h, wx.IMAGE_QUALITY_HIGH)
				wxbmp = img.ConvertToBitmap()
				dc.DrawBitmap(wxbmp, self.x[0], self.y[0], True)

		### Draw lock picture
		if self.lock_flag:
			img =  wx.Bitmap(os.path.join(ICON_PATH_16_16, 'lock.png'), wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap(img, self.x[0], self.y[0])

		### Draw filename path flag picture
		if self.bad_filename_path_flag:
			img = wx.Bitmap(os.path.join(ICON_PATH_16_16, 'flag_exclamation.png'), wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap(img, self.x[0]+15, self.y[0])

		#img = wx.Bitmap(os.path.join(ICON_PATH_16_16, 'atomic3.png'), wx.BITMAP_TYPE_ANY)
		#dc.DrawBitmap( img, self.x[0]+30, self.y[0] )

		### Draw label
		dc.DrawText(self.label, mx, my)

	#def OnResize(self):
		#Shape.OnResize(self)

	###
	def OnLeftUp(self, event):
		pass

	###
	def leftUp(self, event):
		pass

	###
	def OnRightDown(self, event):
		""" Right down event has been invoked.
		"""
		menu = Menu.ShapePopupMenu(self, event)
		### Show popup_menu
		canvas = event.GetEventObject()
		canvas.PopupMenu(menu, event.GetPosition())
		### destroy menu local variable
		menu.Destroy()

	###
	def OnLeftDown(self, event):
		"""
		"""
		if event.ControlDown():
			Selectable.OnRenameFromClick(self, event)
		event.Skip()

	###
	def OnProperties(self, event):
		"""
		"""
		canvas = event.GetEventObject()
		f = AttributeEditor(canvas.GetParent(), wx.ID_ANY, self, canvas)
		f.Show()

	def OnPluginsManager(self, event):
		canvas = event.GetEventObject()
		f = PluginsGUI.ModelPluginsManager(	parent=canvas.GetParent(),
									id=wx.ID_ANY,
									title =_('%s - plugin manager')%self.label,
									size = (700,500),
									style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN,
									model= self)
		f.Show()

	def OnExport(self, event):
		""" Method that export Block.
			OnExport is invoked from Menu.py file and the id of sub_menu allows the selection of the appropriate save method in SaveFile (implemented in Savable.py)
		"""

		mainW = wx.GetApp().GetTopWindow()
		parent = event.GetClientData()
		domain_path = os.path.dirname(self.model_path)

		itemId = event.GetId()
		menu = event.GetEventObject()

		### Export by using right clic menu
		if isinstance(menu, wx.Menu):
			menuItem = menu.FindItemById(itemId)
			ext = menuItem.GetLabel().lower()

			wcd = _('%s Files (*.%s)|*.%s|All files (*)|*')%(ext.upper(), ext, ext)
			save_dlg = wx.FileDialog(parent,
									message = _('Export file as...'),
									defaultDir = domain_path,
									defaultFile = str(self.label)+'.%s'%ext,
									wildcard = wcd,
									style = wx.SAVE | wx.OVERWRITE_PROMPT)

			if save_dlg.ShowModal() == wx.ID_OK:
				path = os.path.normpath(save_dlg.GetPath())
				label = os.path.basename(path)

			save_dlg.Destroy()

		### export (save) by using save button of DetachedFrame
		else:
			path = self.model_path
			label = os.path.basename(path)


		try:
			### Block is Savable
			self.SaveFile(path)

			printOnStatusBar(mainW.statusbar, {0:_('%s Exported')%label, 1:''})

		except IOError, error:
			dlg = wx.MessageDialog(parent, \
								_('Error exported file %s\n')%error, \
								label, \
								wx.OK | wx.ICON_ERROR)
			dlg.ShowModal()

	def update(self, concret_subject = None):
		""" Update method to respond to notify call
		"""

		state = concret_subject.GetState()

		### for all properties
		for prop in state:
			val = state[prop]

			# if behavioral propertie
			if prop in self.args:
				self.args[prop] = val
				# si attribut comportemental definit
				# (donc au moins une simulation sur le modele, parce que les instances DEVS ne sont faites qu'à la simulation)
				# alors on peut mettre a jour dynamiquement pendant la simulation :-)
				# attention necessite une local copy dans le constructeur des model DEVS (generalement le cas lorsqu'on veux réutiliser les param du constructeur dans les methodes)
				devs = self.getDEVSModel()
				if devs is not None:
					setattr(devs, prop, val)

			### if graphical properties, we update the canvas
			elif val != getattr(self, prop):

				if prop == 'label':
					canvas = concret_subject.canvas
					diagram = canvas.GetDiagram()
					if val != "" and ' ' not in val:
						new_label = val
						old_label = getattr(self, prop)

						### update priority list
						if old_label in diagram.priority_list:
							### find index of label priority list and replace it
							i = diagram.priority_list.index(old_label)
							diagram.priority_list[i] = new_label

				### clear manager : direct update only for image_path propertie
				if val not in ('',[],{}) or (prop == 'image_path' and val == ""):
					canvas = concret_subject.canvas
					setattr(self, prop, val)
					if isinstance(canvas, ShapeCanvas):
						canvas.UpdateShapes([self])
					else:
						sys.stderr.write(_('Canvas not updated (has been deleted!)'))

		return state

	###
	def __repr__(self):
		"""
		"""
		s = _("\t Label: %s\n")%self.label
		s += "\t Input/Output: %s,%s\n"%(str(self.input), str(self.output))
		return s

#---------------------------------------------------------
class CodeBlock(Block, Achievable):
	""" CodeBlock(label, inputs, outputs)
	"""

	###
	def __init__(self, label = 'CodeBlock', nb_inputs = 1, nb_outputs = 1):
		""" Constructor.
		"""
		Block.__init__(self, label, nb_inputs, nb_outputs)
		Achievable.__init__(self)

	###
	def __setstate__(self, state):
		""" Restore state from the unpickled state values.
		"""

		python_path = state['python_path']
		model_path = state['model_path']

		new_class = None

		dir_name = os.path.basename(DOMAIN_PATH)

		#print "avant "
		#print python_path
		#print model_path
		#print "\n"

		### if the model path is wrong
		if model_path != '':
			if not os.path.exists(model_path):
				# try to find it in the Domain (firstly)
				if dir_name in python_path:

					path = os.path.join(os.path.dirname(DOMAIN_PATH), relpath(str(model_path[model_path.index(dir_name):]).strip('[]')))

					### try to find it in exportedPathList (after Domain check)
					if not os.path.exists(path):
						mainW = wx.GetApp().GetTopWindow()
						for p in mainW.exportPathsList:
							lib_name = os.path.basename(p)
							if lib_name in path:
								path = p+path.split(lib_name)[-1]

					### if path is always wrong, flag is visible
					if not os.path.exists(path):
						state['bad_filename_path_flag'] = True
					else:
						state['model_path'] = path

						state['python_path'] = os.path.basename(python_path)

						if not state['python_path'].endswith('.py'):
							### we find the python file using re module because path can comes from windows and then sep is not the same and os.path.basename don't work !
							state['python_path'] = os.path.join(path, re.findall("([\w]*[%s])*([\w]*.py)"%os.sep, python_path)[0][-1])
				else:
					state['bad_filename_path_flag'] = True

			### load enventual Plugin
			if 'plugins' in state:
				wx.CallAfter(self.LoadPlugins, (state['model_path']))

		### if the model path is empty and the python path is wrong
		elif not os.path.exists(python_path):

			path = python_path

			### if DOMAIN is in python_path
			if dir_name in python_path:

				### try to find in DOMAIN directory
				path = os.path.join(os.path.dirname(DOMAIN_PATH), relpath(str(python_path[python_path.index(dir_name):]).strip('[]')))

				### try to find it in exportedPathList (after Domain check)
				if not os.path.exists(path):
					mainW = wx.GetApp().GetTopWindow()
					for p in mainW.exportPathsList:
						lib_name = os.path.basename(p)
						if lib_name in path:
							path = p+path.split(lib_name)[-1]
							break
			else:
				### try to find if python_path contains a directory wich is also in Domain
				### subdirectories of Domain
				subdirectories = os.listdir(DOMAIN_PATH)
				### for all directories if the directory is in python_path (excluding the file .py (-1))
				for dir in subdirectories:
					if dir in python_path.split(os.sep)[0:-1]:
						### yes, the python_path is wrong but we find that in the Domain there is a directory with the same name
						a = python_path.split(dir+os.sep)
						path = os.path.join(DOMAIN_PATH,dir,a[-1])
						break

			### if path is always wrong, flag is visible
			if os.path.exists(path):
				state['python_path'] = path
			else:
				state['bad_filename_path_flag'] = True

		### test if args from construcor in python file stored in library (on disk) and args from stored model in dsp are the same
		if os.path.exists(python_path) or zipfile.is_zipfile(os.path.dirname(python_path)):
			cls = Components.GetClass(state['python_path'])
			if not isinstance(cls, tuple):
				args_from_stored_constructor_py = inspect.getargspec(cls.__init__).args[1:]
				args_from_stored_block_model = state['args']
				L = list(set(args_from_stored_constructor_py).symmetric_difference( set(args_from_stored_block_model)))
				if L != []:
					for arg in L:
						#print arg, args_from_stored_constructor_py
						if not arg in args_from_stored_constructor_py:
							sys.stdout.write(_("Warning: %s come is old ('%s' arg is deprecated). We update it...\n"%(state['python_path'],arg)))
							del state['args'][arg]
						else:
							arg_values = inspect.getargspec(cls.__init__).defaults
							index = args_from_stored_constructor_py.index(arg)
							state['args'].update({arg:arg_values[index]})

				### Class redefinition if the class inherite to QuickScope, To_Disk or MessagesCollector

				### find all members that is class
				clsmembers = inspect.getmembers(sys.modules[cls.__name__], inspect.isclass)
				names = map(lambda t: t[0], clsmembers)

				### if model inherite of ScopeGUI, it requires to redefine the class with the ScopeGUI class
				if 'To_Disk' in names or 'MessagesCollector' in names:
					new_class = DiskGUI
				elif ('QuickScope' in names):
					state['xlabel'] = ""
					state['ylabel'] = ""
					new_class = ScopeGUI
				else:
					new_class = None

			else:
				sys.stderr.write(_("Error in setstate for CodeBlock: %s\n"%str(cls)))

		### if the fileName attribut dont exist, we define it into the current devsimpy directory (then the user can change it from Property panel)
		if 'args' in state:
			### find all word containning 'filename' without considering the casse
			m = [re.match('[a-zA-Z]*filename[_-a-zA-Z0-9]*',s, re.IGNORECASE) for s in state['args'].keys()]
			filename_list = map(lambda a: a.group(0), filter(lambda s : s is not None, m))
			### for all filename attr
			for name in filename_list:
				fn = state['args'][name]

				if not os.path.exists(fn):
					#fn_dn = os.path.dirname(fn)
					fn_bn = os.path.basename(relpath(fn))

					### try to redefine the path
					if dir_name in fn:
						fn = os.path.join(HOME_PATH, relpath(str(fn[fn.index(dir_name):]).strip('[]')))
					else:
						fn = os.path.join(HOME_PATH, fn_bn)

					### show flag icon on the block anly for the file with extension (input file)
					if os.path.splitext(fn)[-1] != '':
						state['bad_filename_path_flag'] = True

					state['args'][name] = fn

		####################################" Just for old model
		if 'bad_filename_path_flag' not in state:state['bad_filename_path_flag'] = False
		if 'lock_flag' not in state: state['lock_flag'] = False
		if 'image_path' not in state:
			state['image_path'] = ""
			state['attributes'].insert(3,'image_path')
		if 'font' not in state: state['font'] = [FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, u'Arial']
		if 'font' not in state['attributes']: state['attributes'].insert(3,'font')
		if 'selected' not in state: state['selected'] = False
		if 'label_pos' not in state: state['label_pos'] = 'center'
		if 'input_direction' not in state: state['input_direction'] = 'ouest'
		if 'output_direction' not in state: state['output_direction'] = 'est'
		##############################################

		#print "apres "
		#print state['python_path']
		#print state['model_path']
		#print "\n"

		self.__dict__.update(state)
		if new_class:
			self.__class__ = new_class

	def __getstate__(self):
		"""
		"""
		"""Return state values to be pickled."""
		return Achievable.__getstate__(self)

	###
	def __getattr__(self, name):
		"""Called when an attribute lookup has not found the attribute in the usual places
		"""
		if name == 'dump_attributes':
			return ['model_path', 'python_path', 'args'] + self.GetAttributes()
		else:
			raise AttributeError, name

	def draw(self, dc):

		if self.selected:
			### inform about the nature of the block using icon
			name = 'atomic3.png' if self.model_path != "" else 'pythonFile.png'
			img = wx.Bitmap(os.path.join(ICON_PATH_16_16, name), wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap(img, self.x[1]-20, self.y[0])

		Block.draw(self, dc)

	###
	def OnLeftDClick(self, event):
		""" On left double click event has been invoked.
		"""

		self.OnProperties(event)
		event.Skip()

	###
	def OnSelect(self, event):
		"""
		"""
		self.selected = True

	###
	def OnDeselect(self, event):
		"""
		"""
		self.selected = False

	def update(self, concret_subject = None):
		""" Notify has been invocked
		"""
		state = Block.update(self, concret_subject)

		if isinstance(concret_subject, PropertiesGridCtrl):
			### table and dico of bad flag field (pink colored)
			table = concret_subject.GetTable()
			bad_flag_dico = table.bad_flag

			### set of edited fied and set of bad fied (pink for example)
			edited_field_set = set(state)
			bad_flag_set = set(bad_flag_dico.keys())

			#print bad_flag_set, "must be", bad_flag_set.intersection(edited_field_set), "compared to", edited_field_set
			### if intersection is total, all bad field are has been edited and we test at the end of the loop if all of the paths are right.
			if len(bad_flag_set.intersection(edited_field_set)) == len(bad_flag_set):
				for prop in state:
					### Update the filename flag
					m = [re.match('[a-zA-Z_]*ilename[_-a-zA-Z0-9]*',prop, re.IGNORECASE)]
					filename_list = map(lambda a: a.group(0), filter(lambda s : s is not None, m))
					### for all filename attr
					for name in filename_list:
						val = state[prop]
						# if behavioral propertie
						if prop in self.args:
							### is abs fileName ?
							if os.path.isabs(val):
								### if there is an extention, then if the field path exist we color in red and update the bad_filename_path_flag
								bad_flag_dico.update({prop:not os.path.exists(val) and os.path.splitext(val)[-1] == ''})

				self.bad_filename_path_flag = True in bad_flag_dico.values()

	###
	def __repr__(self):
		""" Text representation.
		"""
		s = Block.__repr__(self)
		s+="\t DEVS module path: %s \n"%str(self.python_path)
		s+="\t DEVSimPy model path: %s \n"%str(self.model_path)
		s+="\t DEVSimPy image path: %s \n"%str(self.image_path)
		return s

#---------------------------------------------------------
class ContainerBlock(Block, Diagram, Structurable):
	""" ContainerBlock(label, inputs, outputs)
	"""

	###
	def __init__(self, label = 'ContainerBlock', nb_inputs = 1, nb_outputs = 1):
		""" Constructor
		"""
		Block.__init__(self, label, nb_inputs, nb_outputs)
		Diagram.__init__(self)
		Structurable.__init__(self)
		self.fill = ['#90ee90']

	###
	def __setstate__(self, state):
		""" Restore state from the unpickled state values.
		"""

		python_path = state['python_path']
		model_path = state['model_path']

		dir_name = os.path.basename(DOMAIN_PATH)

		#print "avant "
		#print state['python_path']
		#print state['model_path']
		#print "\n"

		### if the model path is wrong
		if model_path != '':
			if not os.path.exists(model_path):
				### try to find it in the Domain (firstly)
				if dir_name in python_path:

					path = os.path.join(os.path.dirname(DOMAIN_PATH), relpath(str(model_path[model_path.index(dir_name):]).strip('[]')))

					### try to find it in exportedPathList (after Domain check)
					if not os.path.exists(path):
						mainW = wx.GetApp().GetTopWindow()
						for p in mainW.exportPathsList:
							lib_name = os.path.basename(p)
							if lib_name in path:
								path = p+path.split(lib_name)[-1]

					if os.path.exists(path):
						state['model_path'] = path
						### we find the python file using re module because path can comes from windows and then sep is not the same and os.path.basename don't work !
						state['python_path'] = os.path.join(path, re.findall("([\w]*[%s])*([\w]*.py)"%os.sep, python_path)[0][-1])
					else:
						state['bad_filename_path_flag'] = True
				else:
					state['bad_filename_path_flag'] = True

			### load enventual Plugin
			if 'plugins' in state:
				wx.CallAfter(self.LoadPlugins, (state['model_path']))

			### test if args from construcor in python file stored in library (on disk) and args from stored model in dsp are the same
			if os.path.exists(python_path) or zipfile.is_zipfile(os.path.dirname(python_path)):
				cls = Components.GetClass(state['python_path'])
				if not isinstance(cls, tuple):
					args_from_stored_constructor_py = inspect.getargspec(cls.__init__).args[1:]
					args_from_stored_block_model = state['args']
					L = list(set(args_from_stored_constructor_py).symmetric_difference( set(args_from_stored_block_model)))
					if L != []:
						for arg in L:
							if not arg in args_from_stored_constructor_py:
								sys.stdout.write(_("Warning: %s come is old ('%s' arg is deprecated). We update it...\n"%(state['python_path'],arg)))
								del state['args'][arg]
							else:
								arg_values = inspect.getargspec(cls.__init__).defaults
								index = args_from_stored_constructor_py.index(arg)
								state['args'].update({arg:arg_values[index]})
				else:
					sys.stderr.write(_("Error in setstate for ContainerBlock: %s\n"%str(cls)))

		### if the model path is empty and the python path is wrong
		elif not os.path.exists(python_path):
			if dir_name in python_path:

				path = os.path.join(os.path.dirname(DOMAIN_PATH), relpath(str(python_path[python_path.index(dir_name):]).strip('[]')))
				state['python_path'] = paths

				if not os.path.exists(path):
					state['bad_filename_path_flag'] = True

		####################################" Just for old model
		if 'bad_filename_path_flag' not in state: state['bad_filename_path_flag'] = False
		if 'lock_flag' not in state: state['lock_flag'] = False
		if 'parent' not in state: state['parent'] = None
		if 'image_path' not in state:
			state['image_path'] = ""
			state['attributes'].insert(3,'image_path')
		if 'font' not in state: state['font'] = [FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, u'Arial']
		if 'font' not in state['attributes']: state['attributes'].insert(3,'font')
		if 'selected' not in state: state['selected'] = False
		if 'label_pos' not in state:state['label_pos'] = 'center'
		if 'input_direction' not in state: state['input_direction'] = 'ouest'
		if 'output_direction' not in state: state['output_direction'] = 'est'
		#####################################

		#print "apres "
		#print state['python_path']
		#print state['model_path']
		#print "\n"

		self.__dict__.update(state)

	def __getstate__(self):
		"""Return state values to be pickled."""
		#return Structurable.__getstate__(self)
		return Diagram.__getstate__(self)

	def __getattr__(self, name):
		"""Called when an attribute lookup has not found the attribute in the usual places
		"""

		if name == 'dump_attributes':
			return ['shapes', 'priority_list', 'constants_dico', 'model_path', 'python_path','args'] + self.GetAttributes()
		else:
			raise AttributeError, name

	def draw(self, dc):

		if self.selected:
			### inform about the nature of the block using icon
			img = wx.Bitmap(os.path.join(ICON_PATH_16_16, 'coupled3.png'), wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap(img, self.x[1]-20, self.y[0])

		Block.draw(self, dc)

	###
	def OnSelect(self, event):
		"""
		"""
		self.selected = True

	###
	def OnDeselect(self, event):
		"""
		"""
		self.selected = False

	###
	def OnLeftDClick(self, event):
		""" Left Double Click Event Handel
		"""
		canvas = event.GetEventObject()
		canvas.deselect()

		mainW = wx.GetApp().GetTopWindow()

		frame = DetachedFrame(parent = mainW, title = self.label, diagram = self, name = self.label)
		frame.SetIcon(mainW.GetIcon())
		frame.Show()

	def __repr__(self):
		s = Block.__repr__(self)
		s += _("\t DEVS module: %s \n"%str(self.python_path))
		s+="\t DEVSimPy model path: %s \n"%str(self.model_path)
		s+="\t DEVSimPy image path: %s \n"%str(self.image_path)
		return s

#---------------------------------------------------------
# Nodes
class Node(PointShape):
	""" Node(item, index, cf, type)

		Node class for connection between model.
	"""

	def __init__(self, item, index, cf, t='rect'):
		""" Construcotr.
		"""

		self.item = item	### parent Block
		self.index = index	### number of port
		self.cf = cf		### parent canvas
		self.label = ""		### label of port

		self.lock_flag = False                  # move lock
		PointShape.__init__(self, type = t)

	def showProperties(self):
		""" Call item properties.
		"""
		self.item.showProperties

class ConnectableNode(Node):
	""" ConnectableNode(item, index, cf)
	"""

	def __init__(self, item, index, cf):
		""" Constructor.
		"""
		Node.__init__(self, item, index, cf, t = 'circ')

	def OnLeftDown(self, event):
		""" Left Down click has been invoked
		"""
		### deselect the block to delete the info flag
		self.cf.deselect(self.item)
		event.Skip()

	def HitTest(self,x,y):
		""" Collision detection method.
		"""

		### old model can produce an error
		try:
			r = self.graphic.r
			xx = self.x[0] if isinstance(self.x, array.array) else self.x
			yy = self.y[0] if isinstance(self.y, array.array) else self.y

			return not ((x < xx-r or x > xx+r) or (y < yy-r or y > yy+r))
		except Exception, info:
			sys.stdout.write(_("Error in Hitest for %s : %s\n")%(self,info))
			return False

class INode(ConnectableNode):
	""" INode(item, index, cf)
	"""

	def __init__(self, item, index, cf):
		""" Constructor.
		"""
		ConnectableNode.__init__(self, item, index, cf)

		self.label = "in%d"%self.index

	def OnRightDown(self, event):
		""" Right Down event has been received.
		"""
		pass
		#event.Skip()

	def move(self, x, y):
		""" Move method.
		"""
		self.cf.deselect()
		ci = ConnectionShape()
		ci.setOutput(self.item, self.index)
		ci.x[0], ci.y[0] = self.item.getPortXY('input', self.index)
		self.cf.diagram.shapes.insert(0, ci)
		self.cf.showOutputs()
		self.cf.select(ci)

	def leftUp(self, items):
		""" Left up action has been invocked.
		"""

		cs = items[0]

		#if self.item in cs.touch_list:
			#index = cs.touch_list.index(self.item)
			#del cs.touch_list[index]

		if len(items) == 1 and isinstance(cs, ConnectionShape) and cs.output is None:
			cs.setOutput(self.item, self.index)
			#cs.ChangeForm(ShapeCanvas.CONNECTOR_TYPE)

	def draw(self, dc):
		""" Drawing method.
		"""

		x,y = self.item.getPortXY('input', self.index)
		self.moveto(x, y)

		self.fill = ['#00b400'] #GREEN

		dc.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL))

		### prot number
		#dc.SetPen(wx.Pen(wx.NamedColour('black'), 20))
		#dc.DrawText(str(self.index), self.x-self.graphic.r, self.y-self.graphic.r-2)

		### position of label
		if not isinstance(self.item, Port):
			### prepare label position
			if self.item.input_direction == 'ouest':
				xl = x-30
				yl = y
			elif self.item.input_direction == 'est':
				xl = x+2
				yl = y
			elif self.item.input_direction == 'nord':
				xl = x
				yl = y-18
			else:
				xl = x
				yl = y+2

			### Draw label in port
			dc.DrawText(self.label, xl, yl)

		### Drawing
		PointShape.draw(self, dc)

class ONode(ConnectableNode):
	""" ONode(item, index, cf)
	"""

	def __init__(self, item, index, cf):
		""" Constructor.
		"""
		ConnectableNode.__init__(self, item, index, cf)

		self.label = "out%d"%self.index

	def move(self, x, y):
		""" Moving method.
		"""
		self.cf.deselect()
		ci = ConnectionShape()
		ci.setInput(self.item, self.index)
		ci.x[1], ci.y[1] = self.item.getPortXY('output', self.index)
		self.cf.diagram.shapes.insert(0, ci)
		self.cf.showInputs()
		self.cf.select(ci)

	def leftUp(self, items):
		""" Left up action has been invocked
		"""

		cs = items[0]

		#if self.item in cs.touch_list:
			#index = cs.touch_list.index(self.item)
			#del cs.touch_list[index]

		if len(items) == 1 and isinstance(cs, ConnectionShape) and cs.input is None:
			cs.setInput(self.item, self.index)
			#cs.ChangeForm(ShapeCanvas.CONNECTOR_TYPE)

	def draw(self, dc):
		""" Drawing method
		"""
		x,y = self.item.getPortXY('output', self.index)
		self.moveto(x, y)
		self.fill = ['#ff0000']

		dc.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL))
		#dc.SetPen(wx.Pen(wx.NamedColour('black'), 20))

		### prot number
		#dc.DrawText(str(self.index), self.x-self.graphic.r, self.y-self.graphic.r-2)

		### position of label
		if not isinstance(self.item, Port):
			### perapre label position
			if self.item.output_direction == 'est':
				xl = x+2
				yl = y
			elif self.item.output_direction == 'ouest':
				xl = x-40
				yl = y
			elif self.item.output_direction == 'nord':
				xl = x
				yl = y-20
			else:
				xl = x
				yl = y-2

			### Draw label above port
			dc.DrawText(self.label, xl, yl)

		### Drawing
		PointShape.draw(self, dc)

###
class ResizeableNode(Node):
	""" Resizeable(item, index, cf, type)
	"""

	def __init__(self, item, index, cf, t = 'rect'):
		""" Constructor.
		"""
		Node.__init__(self, item, index, cf, t)

		self.fill = ['#000000'] #BLACK

	def draw(self, dc):
		""" Drawing method.
		"""

		try:
			self.moveto(self.item.x[self.index], self.item.y[self.index])
		except IndexError:
			pass

		PointShape.draw(self, dc)

	def move(self, x, y):
		""" Moving method.
		"""

		lines_shape = self.item

		if self.index == 0:
			X = abs(self.item.x[1] - self.item.x[0]-x)
			Y = abs(self.item.y[1] - self.item.y[0]-y)
		else:
			X = abs(self.item.x[1]+x - self.item.x[0])
			Y = abs(self.item.y[1]+y - self.item.y[0])

		### if no lock
		if not lines_shape.lock_flag:
			### Block and minimal size (50,50) or not Block
			if (isinstance(self.item, Block) and X >= 50 and Y >= 50) or not isinstance(self.item, Block):
				self.item.x[self.index] += x
				self.item.y[self.index] += y
				#self.item.OnResize()

	def OnDeleteNode(self, event):
		"""
		"""
		if isinstance(self.item, ConnectionShape):
			for x in self.item.x:
				if x-3 <= event.GetX() <= x+3:
					y = self.item.y[self.item.x.index(x)]
					if y-3 <= event.GetY() <= y+3:
						self.item.x.remove(x)
						self.item.y.remove(y)

	###
	def OnRightDown(self, event):
		""" Right down event has been invoked.
		"""
		menu = Menu.ShapePopupMenu(self, event)
		### Show popup_menu
		canvas = event.GetEventObject()
		canvas.PopupMenu(menu, event.GetPosition())
		### destroy menu local variable
		menu.Destroy()

#---------------------------------------------------------
class Port(CircleShape, Connectable, Selectable, Attributable, Rotatable, Observer):
	""" Port(x1, y1, x2, y2, label)
	"""

	def __init__(self, x1, y1, x2, y2, label = 'Port'):
		""" Constructor.
		"""

		CircleShape.__init__(self, x1, y1, x2, y2, 30.0)
		Connectable.__init__(self)
		Attributable.__init__(self)
		Rotatable.__init__(self)

		self.SetAttributes(Attributable.GRAPHICAL_ATTR[0:4])

		self.label = label
		### TODO: move to args
		self.AddAttribute('id')
		#self.id = 0
		self.args = {}
		self.lock_flag = False                  # move lock

	def __setstate__(self, state):
		""" Restore state from the unpickled state values.
		"""

		####################################" Just for old model
		if 'r' not in state: state['r'] = 30.0
		if 'font' not in state: state['font'] = [FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, u'Arial']
		if 'label_pos' not in state:
			state['label_pos'] = 'center'
			state['attributes'].insert(1,'label_pos')
		if 'output_direction' not in state: state['output_direction'] ="est"
		if 'input_direction' not in state: state['input_direction'] = "ouest"
		##############################################

		self.__dict__.update(state)

	def draw(self, dc):
		""" Drawing method.
		"""

		CircleShape.draw(self, dc)
		w,h =  dc.GetTextExtent(self.label)

		### label position manager
		if self.label_pos == 'bottom':
			### bottom
			my = int(self.y[1])
		elif self.label_pos == 'top':
			### top
			my = int(self.y[1]-(self.r*2)-14)
		else:
			my = int((self.y[0] + self.y[1])/2.0)-int(h/2.0)

		mx = int(self.x[0])+2

		dc.DrawText(self.label, mx, my)

		if self.lock_flag:
			img =  wx.Bitmap(os.path.join(ICON_PATH_16_16, 'lock.png'),wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap( img, self.x[0]+w/3, self.y[0])

	def leftUp(self, event):
		""" Left up event has been invoked.
		"""
		pass

	###
	def OnRightDown(self, event):
		""" Right down event has been invoked.
		"""
		menu = Menu.ShapePopupMenu(self, event)
		### Show popup_menu
		canvas = event.GetEventObject()
		canvas.PopupMenu(menu, event.GetPosition())
		### destroy menu local variable
		menu.Destroy()

	###
	def OnLeftDown(self, event):
		""" Left down event has been invoked.
		"""

		if event.ControlDown():
			Selectable.OnRenameFromClick(self, event)
		event.Skip()

	def OnProperties(self, event):
		""" Properties of port has been invoked.
		"""
		canvas = event.GetEventObject()
		f = AttributeEditor(canvas.GetParent(), wx.ID_ANY, self, canvas)
		f.Show()

	###
	def OnLeftDClick(self, event):
		""" Left double click event has been invoked.
		"""
		self.OnProperties(event)

	def update(self, concret_subject = None):
		""" Update function linked to notify function (observer pattern)
		"""
		state = concret_subject.GetState()

		for prop in state:
			val = state[prop]
			canvas = concret_subject.canvas
			if val != getattr(self, prop):
				setattr(self, prop, val)
				canvas.UpdateShapes([self])

	def __repr__(self):
		"""
		"""
		s="\t Label: %s\n"%self.label
		return s

#------------------------------------------------------------------
class iPort(Port):
	""" IPort(label)
	"""

	def __init__(self, label = 'iPort'):
		""" Constructor
		"""

		Port.__init__(self, 50, 60, 100, 120, label)
		self.fill= ['#add8e6']          # fill color
		#self.AddAttribute('id')
		self.label_pos = 'bottom'
		self.input = 0
		self.output = 1

	def getDEVSModel(self):
		return self

	def setDEVSModel(self, devs):
		self = devs

	def __repr__(self):
		s = Port.__repr__(self)
		s+="\t id: %d \n"%self.id
		return s

#----------------------------------------------------------------
class oPort(Port):
	""" OPort(label)
	"""

	def __init__(self, label = 'oPort'):
		""" Construcotr
		"""

		Port.__init__(self, 50, 60, 100, 120, label)
		self.fill = ['#90ee90']
		#self.AddAttribute('id')
		self.label_pos = 'bottom'
		self.input = 1
		self.output = 0

	def getDEVSModel(self):
		return self

	def setDEVSModel(self, devs):
		self = devs

	def __repr__(self):
		s = Port.__repr__(self)
		s+="\t id: %d \n"%self.id
		return s

#--------------------------------------------------
class ScopeGUI(CodeBlock):
	""" ScopeGUI(label)
	"""

	def __init__(self, label = 'QuickScope'):
		""" Constructor
		"""

		CodeBlock.__init__(self, label, 1, 0)

		### enable edition on properties panel
		self.AddAttribute("xlabel")
		self.AddAttribute("ylabel")

	def OnLeftDClick(self, event):
		""" Left Double Click has been appeared.
		"""

		# If the frame is call before the simulation process, the atomicModel is not instanciate (Instanciation delegate to the makeDEVSconnection after the run of the simulation process)
		devs = self.getDEVSModel()

		if devs:
			canvas = event.GetEventObject()
			# Call the PlotManager which plot on the canvas depending the atomicModel.fusion option
			PlotGUI.PlotManager(canvas, self.label, devs, self.xlabel, self.ylabel)
		else:
			CodeBlock.OnLeftDClick(self, event)

#------------------------------------------------
class DiskGUI(CodeBlock):
	""" DiskGUI(label)
	"""

	def __init__(self, label='DiskGUI'):
		""" Constructor.
		"""
		CodeBlock.__init__(self, label, 1, 0)

	def OnLeftDClick(self, event):
		""" Left Double Click has been appeared.
		"""
		devs = self.getDEVSModel()

		if devs:
			frame= SpreadSheet.Newt( wx.GetApp().GetTopWindow(),
									wx.ID_ANY,
									_("SpreadSheet %s")%self.label,
									devs,
									devs.comma if hasattr(devs, 'comma') else " ")
			frame.Center()
			frame.Show()
		else:
			CodeBlock.OnLeftDClick(self, event)
