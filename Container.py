# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Container.py ---
#                      --------------------------------
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
# GLOBAL IMPORT
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import builtins

if builtins.__dict__.get('GUI_FLAG',True):
	import wx
	import wx.lib.dragscroller
	import wx.lib.dialogs
	from wx.lib.newevent import NewEvent

	_ = wx.GetTranslation

	from pubsub import pub as Publisher

	AttrUpdateEvent, EVT_ATTR_UPDATE = NewEvent()

	### wx.color has been removed in wx. 2.9
	if hasattr(wx, "Color"):
	    wx.Colour = wx.Color
	else:
	    wx.Color = wx.Colour

	if wx.VERSION_STRING >= '4.0':
		wx.StockCursor = wx.Cursor
else:
	import gettext
	_ = gettext.gettext

import os
import sys
import copy
import re
import pickle
import zipfile
import array

import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec
    
from abc import ABC
from tempfile import gettempdir
from traceback import format_exception
from math import * ### for eval
from collections import Counter

if builtins.__dict__.get('GUI_FLAG', True):
	import ConnectDialog
	import DiagramConstantsDialog
	import SpreadSheet
	import ZipManager
	import DropTarget
	import PlotGUI
	import SimulationGUI
	import PriorityGUI
	import CheckerGUI
	import PluginsGUI
	import WizardGUI

### Color definition
RED = '#d91e1e'
RED_LIGHT = '#f2a2a2'
GREEN = '#90ee90'
BLACK = '#000000'
BLUE = '#add8e6'
ORANGE = '#ffa500'

import Components

if builtins.__dict__.get('GUI_FLAG', True):
	import Menu

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
from Mixins.Abstractable import Abstractable

### for all dsp model build with old version of DEVSimPy
sys.modules['Savable'] = sys.modules['Mixins.Savable']

from Decorators import BuzyCursorNotification, Post_Undo
from Utilities import HEXToRGB, relpath, playSound, sendEvent, getInstance, FixedList, getObjectFromString, getTopLevelWindow, printOnStatusBar
from Patterns.Observer import Subject, Observer

if builtins.__dict__.get('GUI_FLAG',True):
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
	if isinstance(msg, str):
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

			# mainW = wx.GetApp().GetTopWindow()

			### try to find if the error come from devs model
			### paths in traceback
			paths = [a for a in trace if a.split(',')[0].strip().startswith('File')]
			### find if DOMAIN_PATH is in paths list (inverted because traceback begin by the end)
			path = None
			line = None
			fct = None

			### find if DOMAIN_PATH is in the first file path of the trace
			p = paths[-1]
			if DOMAIN_PATH in p or HOME_PATH not in p:
				path,line,fct = p.split(',')[0:3]

		except Exception as info:
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
			wx.MessageBox(_("There is errors in python file.\nTrying to translate error informations: %s %s %s")%(typ, val, tb), _("Error"), wx.OK|wx.ICON_ERROR)

def CheckClass(m):
	""" Check if class is ok and return it.
	"""
	if inspect.isclass(m):
		cls = m
		args = Components.GetArgs(cls)

	elif isinstance(m, Block):
		tempdir = gettempdir()
		if tempdir in os.path.dirname(m.python_path):
			cls = ('','','')
		else:
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
	
	### check devs instance
	devs = getInstance(cls, args)

	### check instance error
	return devs if isinstance(devs, (tuple, Exception)) else None

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

		Structurable.__init__(self)

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
		"""Called when an attribute lookup has not found the attribute in the usual places.
		"""

		if name == 'dump_attributes':
			return ['shapes', 'priority_list', 'constants_dico']
		#=======================================================================
		elif name == 'dump_abstr_attributes':
			return Abstractable.DUMP_ATTR if hasattr(self, 'layers') and hasattr(self, 'current_level') else []
		#=======================================================================
		else:
			raise AttributeError(name)

	@staticmethod
	def makeDEVSGraph(diagram, D = {}, type = object):
		""" Make a formated dictionnary to make the graph of the DEVS Network: {'S1': [{'C1': (1, 0)}, {'M': (0, 1)}], port 1 of S1 is connected to the port 0 of C1...
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
		""" Return the DEVS instance of diagram. Iterations order is very important!
				1. we make the codeblock devs instance
				2. we make the devs port instance for all devsimpy port
				3. we make Containerblock instance
				4. we make the connection
		"""

		#import ReloadModule
		#ReloadModule.recompile("DomainInterface.DomainBehavior")
		#ReloadModule.recompile("DomainInterface.DomainStructure")
		#ReloadModule.recompile("DomainInterface.MasterModel")

		#import DomainInterface.MasterModel
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
			import DomainInterface.MasterModel
			diagram.setDEVSModel(DomainInterface.MasterModel.Master())

		### shape list of diagram
		shape_list = diagram.GetShapeList()
		block_list = {c for c in shape_list if isinstance(c, Block)}
		
		### for all codeBlock shape, we make the devs instance
		for m in block_list:
			
			### class object from python file
			cls = Components.GetClass(m.python_path)

			### Class is wrong ?
			if isinstance(cls, (ImportError, tuple)) or cls is None:
				sys.stdout.write(_('Error making DEVS instances for:\n%s (class:%s)\n'%(m.python_path,str(cls))))
				return False
			else:
				### DEVS model recovery
				devs = getInstance(cls, m.args)

				### Is safe instantiation ?
				if isinstance(devs, tuple):
					return devs
				else:
					devs.name = m.label

			if isinstance(m, CodeBlock):
				### les ports des modeles couples sont pris en charge plus bas dans les iPorts et oPorts
				## ajout des port par rapport aux ports graphiques
				for i in range(m.input):
					devs.addInPort(f'in_{i}')

				for j in range(m.output):
					devs.addOutPort(f'out_{j}')

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
    			###===================================================================
				if hasattr(m, 'layers') and hasattr(m, 'current_level'):
					### level is given by the first stored diagram because m.current is not updated by the spin control
					level = m.layers[0].current_level
					dia = m.layers[level]
					m.shapes = dia.GetShapeList()
					m.priority_list = dia.priority_list or []
					m.constants_dico = dia.constants_dico or {}
				###===================================================================

				Diagram.makeDEVSInstance(m)
		
		###============================================================================= Add abstraction level manager
		if hasattr(diagram, 'current_level') and diagram.current_level>0:

			### Add devs model dam to diagram
			dam = diagram.DAM[diagram.current_level]
			devs_dam = getObjectFromString(dam)
			diagram.addSubModel(devs_dam)

			### Add devs model uam to diagram
			uam = diagram.UAM[diagram.current_level]
			devs_uam = getObjectFromString(uam)
			diagram.addSubModel(devs_uam)

			### inputs/outpus of dam/uam are instantiate depending on the iPort/oPort of diagram 0
			dia_0 = diagram.layers[0]
			shapeL0 = dia_0.GetShapeList()

			for m in (s for s in shapeL0 if isinstance(s, iPort)):
				devs_dam.addInPort()
				diagram.addInPort()

			for m in (s for s in shapeL0 if isinstance(s, oPort)):
				devs_uam.addOutPort()
				diagram.addOutPort()

			for m in (s for s in shape_list if isinstance(s, iPort)):
				devs_dam.addOutPort()

			for m in (s for s in shape_list if isinstance(s, oPort)):
				devs_uam.addInPort()

		###==================================================================================
		### Add abstraction level manager
		###==============================================================================
		if hasattr(diagram, 'current_level') and diagram.current_level>0:
			# for all iPort shape, we make the devs instance
			for i,m in enumerate((s for s in shapeL0 if isinstance(s, iPort))):
				p1 = diagram.getDEVSModel().IPorts[i]
				p2 = devs_dam.IPorts[i]
				Structurable.ConnectDEVSPorts(diagram, p1, p2)
		###==============================================================================
		else:
			for m in (s for s in shape_list if isinstance(s, iPort)):
				### add port to coupled model
				diagram.addInPort()
				assert(len(diagram.getIPorts()) <= diagram.input)

		###==============================================================================
		### Add abstraction level manager
		if hasattr(diagram, 'current_level') and diagram.current_level>0:
			# for all oPort shape, we make the devs instance
			for i,m in enumerate((s for s in shapeL0 if isinstance(s, oPort))):
				p1 = devs_uam.OPorts[i]
				p2 = diagram.getDEVSModel().OPorts[i]
				Structurable.ConnectDEVSPorts(diagram, p1, p2)
				###===============================================================================
		else:
			for m in (s for s in shape_list if isinstance(s, oPort)):
				### add port to coupled model
				diagram.addOutPort()
				assert(len(diagram.getOPorts()) <= diagram.output)

		### Connections
		for m in (s for s in shape_list if isinstance(s, ConnectionShape)):
			m1,n1 = m.input
			m2,n2 = m.output
			if isinstance(m1, Block) and isinstance(m2, Block):
				try:
					p1 = m1.getDEVSModel().OPorts[n1]
				except:
					msg = _("It seems that the number of internal output ports (%d) of the coupled model %s is not enough!\nPlease check this.")%(len(m1.getDEVSModel().OPorts),m1.label)
					sys.stdout.write(msg)
					return msg
				try:
					p2 = m2.getDEVSModel().IPorts[n2]
				except:
					msg = _("It seems that the number of internal input ports (%d) of the coupled model %s is not enough!\nPlease check this.")%(len(m2.getDEVSModel().IPorts),m2.label)
					sys.stdout.write(msg)
					return msg

				Structurable.ConnectDEVSPorts(diagram, p1, p2)

			elif isinstance(m1, Block) and isinstance(m2, oPort):
				### TODO insert devs_uam
				p1 = m1.getDEVSModel().OPorts[n1]

				###==============================================================================
				### Add abstraction level manager
				if hasattr(diagram, 'current_level') and diagram.current_level>0:
					p2 = devs_uam.IPorts[m2.id]
				else:
					p2 = diagram.getDEVSModel().OPorts[m2.id]
				###===============================================================================

				Structurable.ConnectDEVSPorts(diagram, p1, p2)

				#p1 = m1.getDEVSModel().OPorts[n1]
				#p2 = diagram.getDEVSModel().OPorts[m2.id]
				#Structurable.ConnectDEVSPorts(diagram, p1, p2)
			elif isinstance(m1, iPort) and isinstance(m2, Block):
				### TODO insert devs_dam

				###==============================================================================
				### Add abstraction level manager
				if hasattr(diagram, 'current_level') and diagram.current_level>0:
					p1 = devs_dam.OPorts[m1.id]
				else:
					p1 = diagram.getDEVSModel().IPorts[m1.id]
				###===============================================================================

				p2 = m2.getDEVSModel().IPorts[n2]
				Structurable.ConnectDEVSPorts(diagram, p1, p2)

				#p1 = diagram.getDEVSModel().IPorts[m1.id]
				#p2 = m2.getDEVSModel().IPorts[n2]
				#Structurable.ConnectDEVSPorts(diagram, p1, p2)

			# elif isinstance(m1, iPort) and isinstance(m2, oPort):
			# 	###==============================================================================
			# 	### Add abstraction level manager
			# 	if hasattr(diagram, 'current_level') and diagram.current_level>0:
			# 		p1 = devs_dam.OPorts[m1.id]
			# 		p2 = devs_dam.IPorts[m2.id]
			# 	else:
			# 		p1 = diagram.getDEVSModel().IPorts[m1.id]
			# 		p2 = diagram.getDEVSModel().OPorts[m2.id]
			# 	###===============================================================================

			# 	Structurable.ConnectDEVSPorts(diagram, p1, p2)
			else:
				msg = _('Direct connections between ports inside the coupled model %s have been founded.\n There are not considered by the simulation!\n'%(diagram.label))
				sys.stdout.write(msg)
				#return msg

		### update priority_list from shape list 
		### Shape list can be increased or decreased (add or remove shape) without invoke the Priority list dialogue
		diagram.updateDEVSPriorityList()

		### reordered the componentSet of the master before the simulation
		if diagram.priority_list:
			L = []
			devs = diagram.getDEVSModel()
			# si l'utilisateur n'a pas definit d'ordre de priorité pour l'activation des modèles, on la construit
			for label1 in diagram.priority_list:
				for m in devs.getComponentSet():
					label2 = m.getBlockModel().label
					if label1 == label2:
						L.append(m)

			devs.setComponentSet(L)

		return diagram.getDEVSModel()

	def SetParent(self, parent):
		"""
		"""
		assert isinstance(parent, ShapeCanvas)
		self.parent =  parent

	def GetParent(self):
		"""
		"""
		return self.parent

	def GetGrandParent(self):
		"""
		"""
		return self.GetParent().GetParent()

	@BuzyCursorNotification
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

	#@cond_decorator(builtins.__dict__.get('GUI_FLAG',True), StatusBarNotification('Load'))
	def LoadConstants(self, label):
		""" Load Constants to general builtin.
		"""

		if self.constants_dico != {}:
			builtins.__dict__[label] = self.constants_dico

		for s in [c for c in self.GetShapeList() if isinstance(c, ContainerBlock)]:
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

			self.priority_list = [s for s in result if s is not None]

			self.modify = True
			self.parent.DiagramModified()

		dlg = PriorityGUI.PriorityGUI(parent, wx.NewIdRef(), _("Priority Manager"), self.priority_list)
		dlg.Bind(wx.EVT_CLOSE, self.OnClosePriorityGUI)
		dlg.Show()

	def OnInformation(self, event):
		"""
		"""
		stat_dico = self.GetStat({'Atomic_nbr':0, 'Coupled_nbr':0, 'Connection_nbr':0, 'Deep_level':0, 'iPort_nbr':0, 'oPort_nbr':0})
		msg = "".join( [_("Path: %s\n")%self.last_name_saved,
						_("Number of atomic devs models: %d\n")%stat_dico['Atomic_nbr'],
						_("Number of coupled devs models: %d\n")%stat_dico['Coupled_nbr'],
						_("Number of coupling: %d\n")%stat_dico['Connection_nbr'],
						_("Number of deep level (description hierarchy): %d\n")%stat_dico['Deep_level'],
						_("Number of input port models: %d\n")%stat_dico['iPort_nbr'],
						_("Number of output port models: %d\n")%stat_dico['oPort_nbr']]
					)

		dlg = wx.lib.dialogs.ScrolledMessageDialog(self.GetParent(), msg, _("Diagram Information"), style=wx.OK|wx.ICON_EXCLAMATION|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		dlg.ShowModal()

	def OnClosePriorityGUI(self, event):
		""" Method that update the self.priority_list and close the priorityGUI Frame
		"""

		obj = event.GetEventObject()
		self.priority_list = [obj.listCtrl.GetItemText(i) for i in range(obj.listCtrl.GetItemCount())]
		obj.Destroy()

		### we can update the devs priority list during the simulation ;-)
		self.updateDEVSPriorityList()

		event.Skip()

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

		dlg = DiagramConstantsDialog.DiagramConstantsDialog(win, wx.NewIdRef(), title)
		dlg.Populate(self.constants_dico)
		if dlg.ShowModal() == wx.ID_OK:
			self.constants_dico = dlg.GetData()
			dlg.Destroy()

	@BuzyCursorNotification
	def checkDEVSInstance(self, diagram=None, D={}):
		""" Recursive DEVS instance checker for a diagram.

			@param diagram: diagram instance
			@param D: Dictionary of models with the associated error

		"""
		### shape list of diagram
		shape_list = set(diagram.GetShapeList())

		#### for all codeBlock and containerBlock shapes, we make the devs instance
		for m in [s for s in shape_list if isinstance(s, (CodeBlock, ContainerBlock))]:
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
		return D if [m for m in list(D.values()) if m != None] != [] else None

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
				frame = CheckerGUI.CheckerGUI(win, self.DoCheck())
				frame.SetDiagram(self)
				frame.Show()

		### no models in diagram
		else:
			wx.MessageBox(_("Diagram is empty.\n\nPlease, drag-and-drop model from libraries control panel to build a diagram or load an existing diagram."),_('Error Manager'))
	
	@BuzyCursorNotification
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

			### Check if all models doesn't contain errors
			D = self.DoCheck()

			### if there is no error in models
			if D is not None:
				dial = wx.MessageDialog(win, \
									_("There is errors in some models.\n\nDo you want to execute the error manager ?"), \
									_('Simulation Manager'), \
									wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)

				playSound(SIMULATION_ERROR_SOUND_PATH)

				if dial.ShowModal() == wx.ID_YES:
					frame = CheckerGUI.CheckerGUI(win, D)
					frame.SetDiagram(self)
					frame.Show()

				return False

			else:

				### Check if models have the same label
				L = diagram.GetLabelList([])
				if len(L)!=len(set(L)):
					model_with_same_label = [f"-{k}" for k,v in Counter(L).items() if v>1]
					txt = "\n".join(model_with_same_label)							
					wx.MessageBox(_("It seems that the following models have a same label:\n\
									%s\n\
									\nIf you plan to use Flat simulation algorithm, all model must have a unique label.")%txt, _("Simulation Manager"))

				### set the name of diagram
				if isinstance(win, DetachedFrame):
					title = win.GetTitle()
				else:
					nb2 = win.GetDiagramNotebook()
					title =nb2.GetPageText(nb2.GetSelection()).rstrip()

				diagram.label = os.path.splitext(os.path.basename(title))[0]

				## delete all attached devs instances
				diagram.Clean()

				## make DEVS instance from diagram
				master = Diagram.makeDEVSInstance(diagram)

				if not master or isinstance(master,str):
					wx.MessageBox(master, _("Simulation Manager"))
					return False
				## test of filename model attribute
				elif all(model.bad_filename_path_flag for model in [m for m in diagram.GetShapeList() if isinstance(m, Block)] if hasattr(model, 'bad_filename_path_flag')):
					dial = wx.MessageDialog(win, \
										_("You don't make the simulation of the Master model.\nSome models have bad fileName path !"),\
										_('Simulation Manager'), \
										wx.OK | wx.ICON_EXCLAMATION)
					dial.ShowModal()
					return False

				else:

#					pluginmanager.trigger_event('START_DIAGRAM', parent = win, diagram = diagram)

					### clear all log file
					for fn in [f for f in os.listdir(gettempdir()) if f.endswith('.devsimpy.log')]:
						os.remove(os.path.join(gettempdir(),fn))

##					obj = event.GetEventObject()
					# si invocation à partir du bouton dans la toolBar (apparition de la frame de simulation dans une fenetre)
					if isinstance(obj, wx.ToolBar) or 'Diagram' in obj.GetTitle():
						frame = SimulationGUI.SimulationDialog(win, wx.NewIdRef(), _(" %s Simulator"%diagram.label))
						frame.SetMaster(master)
						frame.Show()
					## si invocation par le menu (apparition de la frame de simulation dans le panel)
					elif isinstance(obj, (wx.Menu, wx.Frame)):
						sizer3 = wx.BoxSizer(wx.VERTICAL)
						win.panel3.Show()
						win.SimDiag = SimulationGUI.SimulationDialog(win.panel3, wx.NewIdRef(), _("Simulation Manager"))
						win.SimDiag.SetMaster(master)
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
			wx.MessageBox(_("Diagram is empty.\n\nPlease, drag-and-drop model from libraries control panel to build a diagram or load an existing diagram.."),_('Simulation Manager'))
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
		for cs in [c for c in self.GetShapeList() if isinstance(c, ConnectionShape)]:
			if cs.input is not None and cs.output is not None:
				if shape in cs.input+cs.output:
					self.shapes.remove(cs)

		if isinstance(shape, Block):
			if shape.label in self.priority_list:
				### update priority list
				self.priority_list.remove(shape.label)


		if isinstance(shape, Block):
			### update the devs componentSet
			coupled_devs = self.getDEVSModel()
			devs = shape.getDEVSModel()
			if coupled_devs and devs in coupled_devs.getComponentSet():
				coupled_devs.delToComponentSet([devs])

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
		csList = [a for a in self.shapes if isinstance(a, ConnectionShape)]

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
		""" Get the flat list of Block (Code and Container) shape using recursion process
		"""
		for shape in self.shapes:
			if isinstance(shape, CodeBlock):
				l.append(shape)
			elif isinstance(shape, ContainerBlock):
				l.append(shape)
				shape.GetFlatBlockShapeList(l)
		return l

	def GetFlatCodeBlockShapeList(self):
		""" Get the flat list of CodeBlock shapes using recursion process
		"""
		l = []
		for shape in self.shapes:
			if isinstance(shape, CodeBlock):
				l.append(shape)
			if isinstance(shape, ContainerBlock):
				l.extend(shape.GetFlatCodeBlockShapeList())
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

	def GetConnectionShapeGenerator(self):
		""" Function that return the connection shape generator
		"""
		return (s for s in self.shapes if isinstance(s, ConnectionShape))

	def GetBlockCount(self):
		""" Function that return the number of Block shape
		"""
		return self.GetCodeBlockCount()+self.GetContainerBlockCount()

	def GetCodeBlockCount(self):
		""" Function that return the number of codeBlock shape
		"""
		return self.deletedCodeBlockId.pop() if self.deletedCodeBlockId else self.nbCodeBlock

	def GetContainerBlockCount(self):
		""" Function that return the number of containerBlock shape
		"""
		return self.deletedContainerBlockId.pop() if self.deletedContainerBlockId else self.nbContainerBlock

	def GetiPortCount(self):
		""" Function that return the number of iPort shape
		"""
		return self.deletediPortId.pop() if self.deletediPortId else self.nbiPort

	def GetoPortCount(self):
		""" Function that return the number of oPort shape
		"""
		return self.deletedoPortId.pop() if self.deletedoPortId else self.nboPort

	def Clean(self):
		""" Clean DEVS instances attached to all block model in the diagram.
		"""
		if not self.devsModel:
			return

		for devs in [a for a in list(self.devsModel.getFlatComponentSet().values()) if hasattr(a, 'finish')]:
			try:
				Publisher.unsubscribe(devs.finish, "%d.finished"%(id(devs)))
			except:
				sys.stdout.write(_("Impossible to execute the finish method for the model %s!\n")%devs)
				devs.finish(None)

		self.devsModel.setComponentSet([])

		for m in self.GetShapeList():
			m.setDEVSModel(None)

			if isinstance(m, ConnectionShape):
				m.input[0].setDEVSModel(None)
				m.output[0].setDEVSModel(None)

			if isinstance(m, ContainerBlock):
				m.Clean()

	def GetStat(self, d):
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
			elif isinstance(m, iPort):
				d['iPort_nbr']+=1
			elif isinstance(m, oPort):
				d['oPort_nbr']+=1
			else: 
				sys.stdout.write('Unknowm model!\n')

		return d

	def GetLabelList(self, l=[]):
		""" Get Labels of all models
		"""

		for m in [a for a in self.GetShapeList() if isinstance(a, Block)]:
			l.append(m.label)
			if isinstance(m, ContainerBlock):
				m.GetLabelList(l)
		return l

	def GetName(self):
		""" Return the last name saved
		"""
		return os.path.basename(self.last_name_saved)

# Generic Shape Event Handler---------------------------------------------------
class ShapeEvtHandler(ABC):
	""" Handler class
	"""

	def OnLeftUp(self,event):
		pass

	def OnLeftDown(self,event):
		pass

	def leftUp(self,items):
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
	
	FILL = [BLUE]
	
	def __init__(self, x=[], y=[]):
		""" Constructor
		"""

		self.x = array.array('d',x)                      # list of x coord
		self.y = array.array('d',y)                      # list of y coords
		self.fill= Shape.FILL          # fill color
		self.pen = [self.fill[0] , 1, 100]   # pen color and size / 100 = wx.PENSTYLE_SOLID
		self.font = [FONT_SIZE, 74, 93, 700, u'Arial']

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
				dc.SetFont(wx.Font(10, 74, 93, 700, False, u'Arial'))

	def move(self,x,y):
		""" Move method
		"""
	
		if not self.lock_flag:
			self.x = array.array('d', [v+x for v in self.x])
			self.y = array.array('d', [v+y for v in self.y])
	
			
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
		rect = wx.Rect(int(x),int(y), int(width), int(height))
		r=4.0
		if wx.VERSION_STRING < '4.0':
			dc.DrawRoundedRectangleRect(rect, r)
		else:
			wx.DC.DrawRoundedRectangle(dc, rect, r)

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
		p0 = wx.Point(int(self.x[0]), int(self.y[0]-dy/2))
		p1 = wx.Point(int(self.x[0]), int(self.y[1]+dy/2))
		p2 = wx.Point(int(self.x[1]), int(self.y[0]+dy))
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
		dc.DrawCircle(int((self.x[0]+self.x[1])/2), int((self.y[0]+self.y[1])/2), int(self.r))

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
		
		self.x = array.array('d', [v+x for v in self.x])
		self.y = array.array('d', [v+y for v in self.y])
		self.graphic.move(x,y)

	def HitTest(self, x, y):
		return self.graphic.HitTest(x,y)

	def draw(self,dc):
		"""
		"""
		# Mac's DC is already the same as a GCDC, and it causes
        # problems with the overlay if we try to use an actual
        # wx.GCDC so don't try it.
		if 'wxMac' not in wx.PlatformInfo:
			dc = wx.GCDC(dc)

		self.graphic.pen = self.pen
		self.graphic.fill = self.fill
		self.graphic.draw(dc)

if builtins.__dict__.get('GUI_FLAG',True):
	#-------------------------------------------------------------------------------
	class ShapeCanvas(wx.ScrolledWindow, Abstractable, Subject):
		""" ShapeCanvas class.
		"""

		ID = 0
		CONNECTOR_TYPE = 'direct'

		def __init__(self,\
					 parent,\
		  			id=wx.NewIdRef(), \
				  	pos=wx.DefaultPosition, \
			  		size=(-1,-1), \
				  	style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN, \
				  	name="", \
				  	diagram = None):
			""" Construcotr
			"""
			#super(wx.ScrolledWindow, self).__init__(parent, id, pos, size, style, name)
			wx.ScrolledWindow.__init__(self, parent, id, pos, size, style, name)
			Abstractable.__init__(self, diagram)
			Subject.__init__(self)

			self.SetBackgroundColour(wx.WHITE)
			self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

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

			self.timer = wx.Timer(self, wx.NewIdRef())
			self.f = None

			self.scroller = wx.lib.dragscroller.DragScroller(self)

			self.stockUndo = FixedList(NB_HISTORY_UNDO)
			self.stockRedo = FixedList(NB_HISTORY_UNDO)

			### subject init
			self.canvas = self

			### improve drawing with not condsidering the resizeable  node when connect blocks
			self.resizeable_nedeed = True
			self.refresh_need = True

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
			self.Bind(wx.EVT_IDLE, self.OnIdle)

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
			self.Bind(wx.EVT_TIMER, self.OnTimer)

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
				for s in [shape for shape in self.getSelectedShapes() if not isinstance(shape, ConnectionShape)]:
					s.OnRotateR(event)
				event.Skip()
			elif key == 76 and controlDown:  # Rotate model on the left
				for s in [shape for shape in self.getSelectedShapes() if not isinstance(shape, ConnectionShape)]:
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

			shapes = self.diagram.GetShapeList()
			nodes = self.nodes

			### resizeable node not nedeed for connection process (dragging mouse with left button pressed - see when self.resizeable_nedeed is False)
			if not self.resizeable_nedeed:
				nodes = [n for n in nodes if not isinstance(n,ResizeableNode)]


			items = iter(shapes + nodes)

			for item in items:
				try:
					item.draw(dc)
				except Exception as info:
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
			backBrush = wx.Brush(backColour, wx.BRUSHSTYLE_SOLID)
			pdc.SetBackground(backBrush)
			pdc.Clear()

			### to insure the correct redraw when window is scolling
			### http://markmail.org/thread/hytqkxhpdopwbbro#query:+page:1+mid:635dvk6ntxsky4my+state:results
			self.PrepareDC(pdc)

			self.DoDrawing(pdc)

			del pdc

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
			s = self.getInterceptedShape(event)

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

			### Focus on canvas
			#wx.CallAfter(self.SetFocus)

			event.Skip()

		def GetNodeLists(self, source, target):
			"""
			"""

			# deselect and select target in order to get its list of node (because the node are generated dynamicly)
			self.deselect()
			self.select(target)
			self.select(source)

			nodesList = {n for n in self.nodes if not isinstance(n, ResizeableNode)}

			# list of node list for
			sourceNodeList = [n for n in nodesList if n.item == source and isinstance(n, ONode)]
			targetNodeList = [n for n in nodesList if n.item == target and isinstance(n, INode)]

			self.deselect()

			return (sourceNodeList, targetNodeList)

		def GetBlockModel(self):
			""" Return the generator of block model (not ConnectionShape)
			"""
			for m in self.diagram.shapes:
				if not isinstance(m, ConnectionShape):
					yield m

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
			for s in self.GetBlockModel():
				if s.label == targetName:
					target = s
					break

			### init source and taget node list
			self.sourceNodeList, self.targetNodeList = self.GetNodeLists(source, target)

			# Now we, if the nodes list are not empty, the connection can be proposed form ConnectDialog
			if self.sourceNodeList and self.targetNodeList:
				if len(self.sourceNodeList) == 1 and len(self.targetNodeList) == 1:
					self.makeConnectionShape(self.sourceNodeList[0], self.targetNodeList[0])
				else:
					self.dlgConnection = ConnectDialog.ConnectDialog(wx.GetApp().GetTopWindow(), wx.NewIdRef(), _("Connection Manager"), sourceName, self.sourceNodeList, targetName, self.targetNodeList)
					self.dlgConnection.Bind(wx.EVT_BUTTON, self.OnDisconnect, self.dlgConnection._button_disconnect)
					self.dlgConnection.Bind(wx.EVT_BUTTON, self.OnConnect, self.dlgConnection._button_connect)
					self.dlgConnection.Bind(wx.EVT_CLOSE, self.OnCloseConnectionDialog)
					self.dlgConnection.Show()

				self.DiagramModified()

		def OnDisconnect(self, event):
			""" Disconnect selected ports from connectDialog.
			"""

			label_source, label_target = self.dlgConnection.GetLabelSource(), self.dlgConnection.GetLabelTarget()
		
			# dialog results
			sp,tp = self.dlgConnection.GetSelectedIndex()

			### local variables
			snl = len(self.sourceNodeList)
			tnl = len(self.targetNodeList)

			### flag to inform if there are modifications
			modify_flag = False

			### if selected options are not 'All'
			if sp == tp == 0:
				for cs in list(self.diagram.GetConnectionShapeGenerator()):
					if (cs.getInput()[0].label == label_source and cs.getOutput()[0].label == label_target):
						self.RemoveShape(cs)
						modify_flag = True
			elif sp == 0:
				for cs in list(self.diagram.GetConnectionShapeGenerator()):
					if (cs.getInput()[0].label == label_source and cs.getOutput()[0].label == label_target and cs.getOutput()[1] == tp-1):
						self.RemoveShape(cs)
						modify_flag = True
			elif tp == 0:
				for cs in list(self.diagram.GetConnectionShapeGenerator()):
					if (cs.getInput()[0].label == label_source and cs.getInput()[1] == sp-1 and cs.getOutput()[0].label == label_target):
						self.RemoveShape(cs)
						modify_flag = True
			else:
				for cs in list(self.diagram.GetConnectionShapeGenerator()):
					if (cs.getInput()[1] == sp-1) and (cs.getOutput()[1] == tp-1):
						self.RemoveShape(cs)
						modify_flag = True

			### shape has been modified
			if modify_flag:
				self.DiagramModified()
				self.deselect()
				self.Refresh()

		def OnConnect(self, event):
			""" Connect selected ports from connectDialog.
			"""

			# dialog results
			sp,tp = self.dlgConnection.GetSelectedIndex()

			### local variables
			snl = len(self.sourceNodeList)
			tnl = len(self.targetNodeList)

			### all select are "all"
			if sp == tp == 0:
				for i in range(snl):
					try:
						sn = self.sourceNodeList[i]
						tn = self.targetNodeList[i]
						self.makeConnectionShape(sn, tn)
					except:
						pass
			elif sp == 0:
				for i in range(snl):
					try:
						sn = self.sourceNodeList[i]
						tn = self.targetNodeList[tp]
						self.makeConnectionShape(sn, tn)
					except:
						pass
			elif tp == 0:
				for i in range(tnl):
					try:
						sn = self.sourceNodeList[sp]
						tn = self.targetNodeList[i]
						self.makeConnectionShape(sn, tn)
					except:
						pass
			else:
				sn = self.sourceNodeList[sp-1]
				tn = self.targetNodeList[tp-1]
				self.makeConnectionShape(sn,tn)

			modify_flag = True

			self.Refresh()

		@Post_Undo
		def makeConnectionShape(self, sourceNode, targetNode):
			""" Make new ConnectionShape from input number(sp) to output number (tp)
			"""

			### add the connexion to the diagram
			ci = ConnectionShape()
			self.diagram.shapes.insert(0, ci)

			### connexion
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

			### select the new connection
			self.deselect()
			self.select(ci)

		def OnCloseConnectionDialog(self, event):
			"""
			"""
			### deselection de la dernier connection creer
			self.deselect()
			self.Refresh()

			### Destroy the dialog
			try:
				self.dlgConnection.Destroy()
			except:
				pass
			
			event.Skip()

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
			
			event.Skip()

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
				### TODO: GetFocusedItem failed on Linux!
				sdp = parent.GetItemPyData(parent.GetFocusedItem())
				kargs['specific_domain_path']=sdp

			gmwiz = WizardGUI.ModelGeneratorWizard(**kargs)
			gmwiz.run()

			### just for Mac
			if not gmwiz.canceled_flag:
				return gmwiz
			else:
				return None

		def OnStartWizard(self, event):
			"""
			"""

			obj = event.GetEventObject()

			### if right clic on canvas
			parent = self if isinstance(obj, Menu.ShapeCanvasPopupMenu) else wx.GetApp().GetTopWindow().GetControlNotebook().GetTree()
			gmwiz = ShapeCanvas.StartWizard(parent)

			return gmwiz

		def OnRefreshModels(self, event):
			""" New model menu has been pressed. Wizard is instanciate.
			"""

			diagram = self.GetDiagram()
			for block in diagram.GetFlatBlockShapeList():
				block.status_label = ""
				color = CodeBlock.FILL if isinstance(block, CodeBlock) else ContainerBlock.FILL
				block.fill = color
				
			self.UpdateShapes([self])

		def OnNewModel(self, event):
			""" New model menu has been pressed. Wizard is instanciate.
			"""

			### mouse positions
			xwindow, ywindow = wx.GetMousePosition()
			xm,ym = self.ScreenToClient(wx.Point(int(xwindow), int(ywindow)))

			gmwiz = self.OnStartWizard(event)
			
			# if wizard is finished witout closing
			if gmwiz :
				
				m = Components.BlockFactory.CreateBlock( canvas = self,
													x = xm,
													y = ym,
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

					sys.stdout.write(_("Adding DEVSimPy model: \n"))
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
					try:
						newShape = m.Copy()
					except:
						sys.stdout.write(_('Error in Past'))
					else:
						# store correspondance (for coupling)
						D[m]= newShape
						# move new modele
						newShape.x[0] += 35
						newShape.x[1] += 35
						newShape.y[0] += 35
						newShape.y[1] += 35

						#rename new model with number
						if  re.match(r'^([A-Za-z_])+([0-9]+)', newShape.label):
							number_part = re.findall(r'\d+', newShape.label)[-1]

							### increment the number
							newShape.label = re.sub(r'([0-9]+)', str(int(number_part)+1), newShape.label)
						### label has not number and we add it
						else:
							newShape.label = ''.join([newShape.label,'_1'])

						### adding model
						self.AddShape(newShape)

			### adding connectionShape only if the connection is connected on the two side with blocks.
			for cs in [a for a in L if a.input[0] in D and a.output[0] in D]:
				cs.input = (D[cs.input[0]],cs.input[1])	
				cs.output = (D[cs.output[0]],cs.output[1])
				self.AddShape(cs)

			# specify the operation in status bar
			printOnStatusBar(self.GetTopLevelParent().statusbar, {0:_('Paste'), 1:''})
			
			event.Skip()

		def OnCut(self, event):
			""" Cut menu has been clicked. Copy and delete event.
			"""

			self.OnCopy(event)
			self.OnDelete(event)

			event.Skip()

		def OnDelete(self, event):
			""" Delete menu has been clicked. Delete all selected shape.
			"""

			if len(self.select()) > 1:
				msg = _("Do you really want to delete all selected models?")
				dlg = wx.MessageDialog(self, msg, _("Delete Manager"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

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
			"""
			"""
			self.diagram = d

			self.DiagramModified()
			self.deselect()
			self.Refresh()

		def OnRightUp(self,event):
			"""
			"""
			try:
				self.getInterceptedShape(event).OnRightUp(event)
			except AttributeError:
				pass
			event.Skip()

		def OnRightDClick(self,event):
			"""
			"""
			try:
				self.getInterceptedShape(event).OnRightDClick(event)
			except AttributeError:
				pass

			event.Skip()

		def OnLeftDClick(self,event):
			"""
			"""
			model = self.getInterceptedShape(event)
			if model:
			#try:
				model.OnLeftDClick(event)
			#except Exception, info:
			#	wx.MessageBox(_("An error is occured during double clic: %s")%info)
			event.Skip()

		def Undo(self):
			"""
			"""

			mainW = self.GetTopLevelParent()

			### dump solution
			### if parent is not none, the dumps dont work because parent is copy of a class
			try:
				t = pickle.loads(self.stockUndo[-1])

				### we add new undo of diagram has been modified or one of the shape in diagram sotried in stockUndo has been modified.
				if any(objA.__dict__ != objB.__dict__ for objA in self.diagram.GetShapeList() for objB in t.GetShapeList()):
					self.stockUndo.append(pickle.dumps(obj=self.diagram, protocol=0))
			except IndexError:
				### this is the first call of Undo and StockUndo is empty
				self.stockUndo.append(pickle.dumps(obj=self.diagram, protocol=0))
			except TypeError as info:
				sys.stdout.write(_("Error trying to undo (TypeError): %s \n"%info))
			except Exception as info:
				sys.stdout.write(_("Error trying to undo: %s \n"%info))
			else:

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
			item = self.getInterceptedShape(event)

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
				if isinstance(event,wx.MouseEvent):
					# point = event.GetPosition()
					point = self.getEventCoordinates(event)
					self.selectionStart = point

			elif item not in self.getSelectedShapes():

				item.OnLeftDown(event) # send leftdown event to current shape
				if isinstance(item, Selectable) and not event.ControlDown():
					self.deselect()

				self.select(item)

			else:

				for s in self.getSelectedShapes():
					s.OnLeftDown(event) # send leftdown event to current shape

				self.deselect(item)

			### Update the nb1 panel properties only for Block and Port (call update in ControlNotebook)
			win = getTopLevelWindow()
			nb1 = win.GetControlNotebook()
			pos = nb1.GetSelection()
			txt = nb1.GetPageText(pos)

			### Update the editor panel (on the right by default) when a block is selected
			mgr = win.GetMGR()
			mgr.GetPane("editor")

			if (mgr.GetPane("editor").IsShown() or txt.startswith('Prop')) and isinstance(item, Attributable):
				self.__state['model'] = item
				self.__state['canvas'] = self

				self.notify()

			# self.Refresh()
			event.Skip()

		###
		@Post_Undo
		def OnLeftUp(self, event):
			"""
			"""

			cursor = self.GetCursor()
		
			if cursor != wx.StockCursor(wx.CURSOR_ARROW):
				self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
			
			### intercepted shape
			shape = self.getInterceptedShape(event)
			
			### if connection is being, then we try to avoid the bug that appears when the mouse coursor and the end of the connection are superposed.
			### So, x and y is the coordinate of the end of the connection and we try to find the shape targeted by the connection (Block or Port shape type)
			### If HitTest between the point and the targeted shape and if the the getInterceptedShape dont return a Node (whiwh is the case when the cross appears to connect)
			### the targeted shape is the returned.
			if isinstance(shape, ConnectionShape):
				cs = shape
				x = cs.x[0] if not cs.input else cs.x[-1]
				y = cs.y[0] if not cs.output else cs.y[-1]
				
				for s in iter(s for s in self.diagram.shapes if isinstance(s, (Block,Port))):
					if s.HitTest(x,y) and s != cs:
						shape = s
						break
			
			### if cursor of mouse is in connectionShape (drag slowly), getInterceptedShape return the connectionShape Block.
			### So, if the connectionShape is not connected, shape is none and the connectionShape is not drawed.
			### If we left up on an existing connectionShape, nothing append
			if isinstance(shape,ConnectionShape) and (not shape.input or not shape.output):
				shape = None

			self.resizeable_nedeed = True

			### clic sur un block ou un node pour connection à block
			if shape:

				shape.OnLeftUp(event)
				shape.leftUp(self.select())

				remove = True
				
				### connectionShape
				cs = next(iter(s for s in self.select() if isinstance(s, ConnectionShape)),None)

				if cs:
				### empty connection manager
				#for cs in [s for s in self.select() if isinstance(s, ConnectionShape)]:
					### restore solid connection
					if len(cs.pen)>2:
						cs.pen[2]= 100 #wx.PENSTYLE_SOLID

					### if left up on block
					if None in (cs.output, cs.input):
						
						### new link request
						dlg = wx.TextEntryDialog(self, _('Choose the port number.\nIf doesn\'t exist, we create it.'),_('Coupling Manager'))
						if cs.input is None:
							if isinstance(shape,Port):
								dlg.SetValue('0')
							else:
								if hasattr(shape, 'output'):
									dlg.SetValue(str(shape.output))
								else:
									dlg.Destroy()

							if dlg.ShowModal() == wx.ID_OK:
								try:
									val=int(dlg.GetValue())
								### is not digit
								except ValueError:
									pass
								else:
									if val >= shape.output:
										nn = shape.output
										shape.output+=1
									else:
										nn = val
									cs.input = (shape, nn)
									### dont abort the link
									remove = False
						else:
							if isinstance(shape,Port):
								dlg.SetValue('0')
							else:
								if hasattr(shape, 'input'):
									dlg.SetValue(str(shape.input))
								else:
									dlg.Destroy()

							if dlg.ShowModal() == wx.ID_OK:
								try:
									val=int(dlg.GetValue())
								### is not digit
								except ValueError:
									pass
								else:
									if val >= shape.input:
										nn = shape.input
										shape.input+=1
									else:
										nn = val
									cs.output = (shape, nn)
									### dont abort the link
									remove = False

						if remove:
							self.diagram.DeleteShape(cs)
							self.deselect()
					else:
						### transformation de la connection en zigzag
						pass

			### click on canvas
			else:
				### Rubber Band with overlay
				## User released left button, change cursor back
				if self.HasCapture():
					try:
						self.ReleaseMouse()
					except:
						sys.stdout.write(_("Error in Release Mouse!"))
					else:
						self.permRect = None
						if isinstance(event,wx.MouseEvent):
							point = self.getEventCoordinates(event)
							if self.selectionStart != point:
								self.permRect = wx.Rect(self.selectionStart, point)
						
						if self.permRect:

							self.selectionStart = None
							self.overlay.Reset()

							self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

							## gestion des shapes qui sont dans le rectangle permRect
							for s in self.diagram.GetShapeList():
								x,y = self.getScalledCoordinates(s.x[0],s.y[0])
								w = (s.x[1]-s.x[0])*self.scalex
								h = (s.y[1]-s.y[0])*self.scaley
								
								recS = wx.Rect(int(x),int(y),int(w),int(h))

								# rect hit test
								if self.permRect.Contains(recS):
									self.select(s)
				else:
				
					### shape is None and we remove the connectionShape
					for item in [s for s in self.select() if isinstance(s, ConnectionShape)]:
						self.diagram.DeleteShape(item)
						self.deselect()

			self.Refresh()

			event.Skip()

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

				This method manage the propagation of modification.
				from window where modifications are performed to DEVSimPy main window.
			"""

			if not self.diagram.modify:
				return

			### window where modification is performed
			win = self.GetTopLevelParent()

			if isinstance(win, DetachedFrame):
				### main window
				mainW = wx.GetApp().GetTopWindow()

				if not isinstance(mainW, DetachedFrame) and hasattr(mainW, 'GetDiagramNotebook'):
					nb2 = mainW.GetDiagramNotebook()
					s = nb2.GetSelection()
					canvas = nb2.GetPage(s)
					diagram = canvas.GetDiagram()
					### modifying propagation
					diagram.modify = True
					### update general shapes
					canvas.UpdateShapes()

					label = nb2.GetPageText(s)

					### modified windows dictionary
					D = {win.GetTitle(): win, label: mainW}
				else:
					D={}
			else:
				nb2 = win.GetDiagramNotebook()
				s = nb2.GetSelection()
				canvas = nb2.GetPage(s)
				diagram = canvas.GetDiagram()
				diagram.modify = True
				label = nb2.GetPageText(s)

				D = {label : win}

			### update the text of the notebook tab to notifiy that the file is modified
			nb2.SetPageText(nb2.GetSelection(), "%s*"%label.replace('*',''))

			### statusbar printing
			for string,win in list(D.items()):
				printOnStatusBar(win.statusbar, {0:"%s %s"%(string.replace('*','') ,_("modified")), 1:diagram.last_name_saved, 2:''})

			### update the toolbar
			tb = win.GetToolBar()
			tb.EnableTool(Menu.ID_SAVE, self.diagram.modify)

		def ShowQuickAttributeEditor(self, selectedShape:list)->None:
			""" Show a quick dialog with spin to change the number of imput and output of the block.
			"""

			mainW = self.GetTopLevelParent()

			flag = True
			### find if window exists on the top of model, then inactive the QuickAttributeEditor
			for win in [w for w in mainW.GetChildren() if w.IsTopLevel()]:
				if win.IsActive():
					flag = False

			if self.f:
				self.f.Close()
				self.f = None

			if flag:
				# mouse positions
				xwindow, ywindow = wx.GetMousePosition()
				xm,ym = self.ScreenToClient(wx.Point(int(xwindow), int(ywindow)))

				for s in {m for m in selectedShape if isinstance(m, Block)}:
					x = s.x[0]*self.scalex
					y = s.y[0]*self.scaley
					w = s.x[1]*self.scalex-x
					h = s.y[1]*self.scaley-y

					# if mousse over hight the shape
					try:

						if (x<=xm and xm < x+w) and (y<=ym and ym < y+h):
							#if self.isSelected(s) and flag:
							self.f = QuickAttributeEditor(self, wx.NewIdRef(), s)
							self.timer.Start(1000)
							break
						else:
							if self.timer.IsRunning():
								self.timer.Stop()

					except AttributeError as info:
						raise AttributeError(_("use >= wx-2.8-gtk-unicode library: %s")%info)

		def OnIdle(self,event):
			"""
			"""
			if self.refresh_need:
				self.Refresh(False)
		
		###
		def OnMotion(self, event):
			""" Motion manager.
			""" 

			### current cursor
			cursor = self.GetCursor()

			sc = self.getSelectedShapes()

			self.refresh_need = True
			self.resizeable_nedeed = True

			if event.Dragging() and event.LeftIsDown():

				self.diagram.modify = False
				

				if len(sc) == 0:
					# User is dragging the mouse, check if
					# left button is down
					if self.HasCapture():

						if cursor != wx.StockCursor(wx.CURSOR_ARROW):
							cursor = wx.StockCursor(wx.CURSOR_ARROW)
						
						dc = wx.ClientDC(self)
						odc = wx.DCOverlay(self.overlay, dc)
						odc.Clear()
						ctx = wx.GraphicsContext.Create(dc)

						ctx.SetPen(wx.GREY_PEN)
						ctx.SetBrush(wx.Brush(wx.Colour(229,229,229,80)))
						
						try:
							ctx.DrawRectangle(*wx.Rect(self.selectionStart, event.GetPosition()))
						except TypeError:
							pass

						del odc

						### no need to refresh in order to qhpw the rectangle
						self.refresh_need = False
					# else:
						# self.Refresh(False)
				else:
					
					point = self.getEventCoordinates(event)
					
					x = point[0] - self.currentPoint[0]
					y = point[1] - self.currentPoint[1]

					if cursor != wx.StockCursor(wx.CURSOR_HAND):
						cursor = wx.StockCursor(wx.CURSOR_HAND)
				
					for s in sc:
						s.move(x,y)

						### change cursor when resizing model
						if isinstance(s, ResizeableNode) and cursor != wx.StockCursor(wx.CURSOR_SIZING):
							cursor = wx.StockCursor(wx.CURSOR_SIZING)

						### change cursor when connectionShape hit a node
						elif isinstance(s, ConnectionShape):

							### dot trace to prepare connection
							if len(s.pen)>2:
								s.pen[2]= wx.PENSTYLE_DOT

							if cursor != wx.StockCursor(wx.CURSOR_HAND):
								cursor = wx.StockCursor(wx.CURSOR_HAND)

							for node in [n for n in self.nodes if isinstance(n, ConnectableNode) and n.HitTest(point[0], point[1])]:
								if cursor != wx.StockCursor(wx.CURSOR_CROSS):
									cursor = wx.StockCursor(wx.CURSOR_CROSS)

							self.resizeable_nedeed = False
							
					### update the cursor
					self.SetCursor(cursor)
					### update modify
					self.diagram.modify = True
					### update current point
					self.currentPoint = point

					### refresh all canvas with Flicker effect corrected in OnPaint and OnEraseBackground
					# self.Refresh(False)
					
					
			# pop-up to change the number of ports
			else:
				point = self.getEventCoordinates(event)
			
				### restor the cursor with arrow
				if cursor != wx.StockCursor(wx.CURSOR_ARROW):
					cursor = wx.StockCursor(wx.CURSOR_ARROW)

				for node in self.nodes:
					if node.HitTest(point[0],point[1]):
						### change the cursor when node is pointed
						if isinstance(node, ResizeableNode) and cursor != wx.StockCursor(wx.CURSOR_SIZING):
							cursor = wx.StockCursor(wx.CURSOR_SIZING)
						elif isinstance(node, ConnectableNode) and cursor != wx.StockCursor(wx.CURSOR_CROSS):
							cursor = wx.StockCursor(wx.CURSOR_CROSS)
				
				### update the cursor
				self.SetCursor(cursor)

				if len(sc) != 0:
					### show the quick attribut editor
					self.ShowQuickAttributeEditor(sc)
			
			event.Skip()

			#self.DiagramModified()

#		def SetDiagram(self, diagram):
#			""" Setter for diagram attribute.
#			"""
#			self.diagram = diagram		def SetDiagram(self, diagram):
#			""" Setter for diagram attribute.
#			"""
#			self.diagram = diagram

		def GetDiagram(self):
			""" Return Diagram instance.
			"""
			return self.diagram

		def getInterceptedShape(self, event, exclude=[]):
			""" Return the intercepted current shape.
			"""
			# get coordinate of click in our coordinate system
			if isinstance(event, wx.MouseEvent):
				point = self.getEventCoordinates(event)
				self.currentPoint = point
			elif isinstance(event, wx.Point):
				point = event
				self.currentPoint = point
			else:
				return None

			# Look to see if an item is selected
			for item in self.nodes + self.diagram.shapes:
				if item.HitTest(point[0], point[1]) and item not in exclude:
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
			return (s) and (s in self.getSelectedShapes()) or isinstance(s, ConnectableNode)

		def getName(self):
			""" Return the name
			"""
			return self.name

		def deselect(self, item=None):
			""" Deselect all shapes
			"""

			if item is None:
				for s in self.getSelectedShapes():
					s.OnDeselect(None)
				del self.selectedShapes[:]
				del self.nodes[:]
			else:
				self.nodes = [ n for n in self.nodes if n.item != item]
				self.selectedShapes = [ n for n in self.getSelectedShapes() if n != item]
				item.OnDeselect(None)

		### selectionne un shape
		def select(self, item=None):
			""" Select the models in param item
			"""

			if item is None:
				return self.getSelectedShapes()

			if isinstance(item, Node):
				del self.selectedShapes[:]
				self.selectedShapes.append(item) # items here is a single node
				return

			if not self.isSelected(item):
				
				self.selectedShapes.append(item)
					
				item.OnSelect(None)

				if isinstance(item, Connectable):
					### display the label of input ports if exist
					for n in range(item.input):
						self.nodes.append(INode(item, n, self, item.getInputLabel(n)))

					### display the label of output ports if exist
					for n in range(item.output):
						self.nodes.append(ONode(item, n, self, item.getOutputLabel(n)))
				
				### display the label of port attahced to the connection shape (make more easy the correspondance of the link)
				if isinstance(item, ConnectionShape):
					
					if item.input:
						block, n = item.input
						self.nodes.append(ONode(block, n, self, block.getOutputLabel(n)))

					if item.output:
						block, n = item.output
						self.nodes.append(INode(block, n, self, block.getInputLabel(n)))
					
				if isinstance(item, Resizeable):
					self.nodes.extend([ResizeableNode(item, n, self) for n in range(len(item.x))])
					
			return 

		###
		def UpdateShapes(self, L=None):
			""" Method that update the graphic of the models composing the parameter list.
			"""

			# update all models in canvas
			if L is None:
				L = self.diagram.shapes

			# select all models in selectedList and refresh canvas
			for m in [a for a in L if self.isSelected(a)]:
				self.deselect(m)
				self.select(m)
			
			self.Refresh()

		### selection sur le canvas les ONodes car c'est le seul moyen d'y accéder pour effectuer l'appartenance avec les modèles
		def showOutputs(self, item=None):
			""" Populate nodes list with output ports.
			"""
			if item:
				self.nodes.extend([ONode(item, n, self, item.getInputLabel(n)) for n in range(item.output)])
			else:
				for s in [a for a in self.diagram.shapes if isinstance(a, Connectable)]:
					self.nodes.extend([ONode(s, n, self, s.getInputLabel(n)) for n in range(s.output)])

		### selection sur le canvas les INodes car c'est le seul moyen d'y accéder pour effectuer l'appartenance avec les modèles
		def showInputs(self,item=None):
			""" Populate nodes list with output ports.
			"""
			if item:
				self.nodes.extend([INode(item, n, self,  item.getInputLabel(n)) for n in range(item.input)])
			else:
				for s in [a for a in self.diagram.shapes if isinstance(a, Connectable)]:
					self.nodes.extend([INode(s, n, self, s.getInputLabel(n)) for n in range(s.input)])

		def GetState(self):
			return self.__state

#-----------------------------------------------------------
class LinesShape(Shape):
	""" Line Shape Class.
	"""

	def __init__(self, line):
		""" Constructor.
		"""
		Shape.__init__(self)

		self.fill = [RED]
		self.x = array.array('d', line.x)
		self.y = array.array('d', line.y)

	def draw(self, dc):
		""" Drawing line.
		"""
		Shape.draw(self, dc)

		L = list(zip(self.x,self.y)) #list(map(lambda a,b: (a,b), self.x, self.y))

		### line width
		w = self.x[1] - self.x[0]

		### update L depending of the connector type
		if ShapeCanvas.CONNECTOR_TYPE == 'linear':
			
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
			L.insert(1,(self.x[0]+w/2, self.y[0]))
			L.insert(2,(self.x[0]+w/2, self.y[1]))

		else:
			pass

		dc.DrawLines(L)
	
		### pour le rectangle en bout de connexion
		dc.SetBrush(wx.Brush(RED_LIGHT))
		pt1 = wx.Point(int(self.x[-1]-10/2), int(self.y[-1]-10/2)) 
		pt2 = wx.Point(int(self.x[0]-10/2), int(self.y[0]-10/2))
		wx.DC.DrawRectangle(dc, pt1, wx.Size(10, 10))
		wx.DC.DrawRectangle(dc, pt2, wx.Size(10, 10))
		
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

		try:
			### mouse positions
			if wx.VERSION_STRING < '4.0':
				x,y = event.GetPositionTuple()
			else:
				xwindow, ywindow = wx.GetMousePosition()
				x,y = canvas.ScreenToClient(wx.Point(int(xwindow), int(ywindow)))

		except Exception as info:
			sys.stdout.write(_("Error in OnLeftDClick for %s : %s\n")%(self,info))
		else:
			### add point at the position according to the possible zoom (use of getScalledCoordinates)
			self.AddPoint(canvas.getScalledCoordinates(x,y))

		event.Skip()

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
		for i in range(len(self.x)-1):
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
		if L:

			#model_path = os.path.dirname(self.python_path)

			# TODO: Testable :: OnTestEditor => Fix Editor importation
			import Editor

			#mainW = wx.GetApp().GetTopWindow()
			### Editor instanciation and configuration---------------------
			editorFrame = Editor.GetEditor(
					None,
					wx.NewIdRef(),
					'Features',
					file_type="test"
			)

			for i,s in enumerate([os.path.join(self.model_path, l) for l in L]):
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
		fn = os.path.dirname(self.python_path)
		return zipfile.is_zipfile(fn) and fn.endswith(('.amd')) if os.path.isfile(fn) else False

	def isCMD(self):
		fn = os.path.dirname(self.python_path)
		return zipfile.is_zipfile(fn) and fn.endswith(('.cmd')) if os.path.isfile(fn) else False

	def isPYC(self):
		return self.python_path.endswith('.pyc') if os.path.isfile(self.python_path) else False

	def isPY(self):
		return self.python_path.endswith('.py') if os.path.isfile(self.python_path) else False

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

		feat_name = [t for t in tests_files if t.endswith('.feature')][0]
		featInfo = importer.getinfo(feat_name)
		feat_code = importer.read(featInfo)

		steps_name = [t for t in tests_files if t.endswith('steps.py')][0]
		stepsInfo = importer.getinfo(steps_name)
		steps_code = importer.read(stepsInfo)

		if not global_env:
			environment_name = [t for t in tests_files if t.endswith('environment.py')][0]
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
				for name in dirs: os.rmdir(os.path.join(root, name))

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
		if 'font' not in state: state['font'] = [FONT_SIZE, 74, 93, 700, u'Arial']
		##############################################

		self.__dict__.update(state)

	def setInput(self, item, index):
		"""
		"""
		self.input = (item, index)

	def setOutput(self, item, index):
		"""
		"""
		self.output = (item, index)

	def getInput(self):
		"""
		"""
		return self.input

	def getOutput(self):
		"""
		"""
		return self.output

	def draw(self, dc):
		"""
		"""

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
		event.Skip()

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
		event.Skip()
	
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

		# Mac's DC is already the same as a GCDC, and it causes
        # problems with the overlay if we try to use an actual
        # wx.GCDC so don't try it.
		if 'wxMac' not in wx.PlatformInfo:
			dc = wx.GCDC(dc)

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
				sourceZip.extract(str(image_name), gettempdir())
				sourceZip.close()
			else:
				image_path = self.image_path

			if os.path.isabs(image_path):
				img = wx.Image(image_path).Scale(self.w, self.h, wx.IMAGE_QUALITY_HIGH)
				wxbmp = img.ConvertToBitmap()
				dc.DrawBitmap(wxbmp, int(self.x[0]), int(self.y[0]), True)

		### Draw lock picture
		if self.lock_flag:
			img =  wx.Bitmap(os.path.join(ICON_PATH_16_16, 'lock.png'), wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap(img, int(self.x[0]), int(self.y[0]))

		### Draw filename path flag picture
		if self.bad_filename_path_flag:
			img = wx.Bitmap(os.path.join(ICON_PATH_16_16, 'flag_exclamation.png'), wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap(img, int(self.x[0]+15), int(self.y[0]))

		#img = wx.Bitmap(os.path.join(ICON_PATH_16_16, 'atomic3.png'), wx.BITMAP_TYPE_ANY)
		#dc.DrawBitmap( img, self.x[0]+30, self.y[0] )

		### Draw label
		dc.DrawText(self.label, int(mx), int(my))

		if hasattr(self,'status_label'):
			dc.DrawText(self.status_label, int(mx), int(my+20))
		else:
			self.status_label = ""

	#def OnResize(self):
		#Shape.OnResize(self)

	###
	def OnLeftUp(self, event):
		event.Skip()

	###
	def leftUp(self, items):
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
		event.Skip()

	###
	#def OnLeftDown(self, event):
	#	"""
	#	"""
		
		### Change the label of block
		#if event.ControlDown():
		#	Selectable.OnRenameFromClick(self, event)	
	#	event.Skip()

	###
	def OnProperties(self, event):
		"""
		"""
		canvas = event.GetEventObject()
		f = AttributeEditor(canvas.GetParent(), wx.NewIdRef(), self, canvas)
		f.Show()
		
	def OnPluginsManager(self, event):
		"""
		"""
		canvas = event.GetEventObject()
		f = PluginsGUI.ModelPluginsManager(	parent=canvas.GetParent(),
									id=wx.NewIdRef(),
									title =_('%s - plugin manager')%self.label,
									size = (700,500),
									style = wx.LC_REPORT| wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN,
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

		path = None

		### Export by using right clic menu
		if isinstance(menu, wx.Menu):
			menuItem = menu.FindItemById(itemId)
			ext = menuItem.GetItemLabel().lower()

		### export (save) by using save button of DetachedFrame
		else:
			ext = 'cmd'

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
		#else:
		#	path = self.model_path
		#	label = os.path.basename(path)

		if path:
			try:

				### Block is Savable
				self.SaveFile(path)
				
				printOnStatusBar(mainW.statusbar, {0:_('%s Exported')%label, 1:''})

			except IOError as error:
				dlg = wx.MessageDialog(parent, \
									_('Error exported file %s\n')%error, \
									label, \
									wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()

	def update(self, concret_subject = None):
		""" Update method to respond to notify call.
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

				### clear custom port labels if their number change 
				# if prop == 'input':
					# self.setInputLabels({})
				# if prop == 'output':
					# self.setOutputLabels({})

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
		return "".join([_("\n\t Label: %s\n")%self.label,
						_("\t Input/Output: %s,%s\n")%(str(self.input), str(self.output))]
						)

#---------------------------------------------------------
class CodeBlock(Achievable, Block):
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
		image_path = state['image_path']
		new_class = None
		dir_name = os.path.basename(DOMAIN_PATH)

		### if the model path is wrong
		if model_path != '':
			if not os.path.exists(model_path):
				# try to find it in the Domain (firstly)
				if dir_name in python_path:

					path = os.path.join(os.path.dirname(DOMAIN_PATH), relpath(str(model_path[model_path.index(dir_name):]).strip('[]')))

					print(path)
					### perhaps path is wrong due to a change in the Domain lib !
					### Try to find the model by its name in the Domain directories (multipe path can be occur)
#					if not os.path.exists(path):
#						file_name = os.path.basename(path)
#						for root, dirs, files in os.walk(DOMAIN_PATH):
#							for name in files:
#								if name == file_name:
#									path = os.path.abspath(os.path.join(root, name))

					### try to find it in exportedPathList (after Domain check)
					if not os.path.exists(path) and builtins.__dict__.get('GUI_FLAG',True):
						import wx
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

						python_filename = os.path.basename(python_path)

						if str(python_filename).find('\\'):
							### wrong basename :
							### os.path.basename does not work when executed on Unix
							### with a Windows path
							python_path = python_path.replace('\\','/')
							python_filename = os.path.basename(python_path)

						state['python_path'] = os.path.join(state['model_path'] , python_filename)

						if not state['python_path'].endswith('.py'):
							### Is this up-to-date???
							### we find the python file using re module
							### because path can comes from windows and then sep is not the same and os.path.basename don't work !
							state['python_path'] = os.path.join(path, re.findall("([\w]*[%s])*([\w]*.py)"%os.sep, python_path)[0][-1])
				else:
					state['bad_filename_path_flag'] = True

			### load enventual Plugin
			if 'plugins' in state and builtins.__dict__.get('GUI_FLAG',True):
				wx.CallAfter(self.LoadPlugins, (state['model_path']))

		### test if args from construcor in python file stored in library (on disk) and args from stored model in dsp are the same
		if os.path.exists(python_path) or zipfile.is_zipfile(os.path.dirname(python_path)):
		
			cls = Components.GetClass(state['python_path'])
			
			### TODO
			### local package imported into amd or cmd generates error ! (fcts...)
			if cls and not isinstance(cls, tuple):
				try:
					args_from_stored_constructor_py = inspect.getargspec(cls.__init__).args[1:]
				except ValueError:
					constructor = inspect.signature(cls.__init__)
					parameters = constructor.parameters
					args_from_stored_constructor_py = [name for name, _ in parameters.items() if name != 'self']

				args_from_stored_block_model = state['args']
				L = list(set(args_from_stored_constructor_py).symmetric_difference(set(args_from_stored_block_model)))
				if L:
					for arg in L:
						if not arg in args_from_stored_constructor_py:
							sys.stdout.write(_("Warning: %s come is old ('%s' arg is deprecated). We update it...\n"%(state['python_path'],arg)))
							del state['args'][arg]
						else:
							try:
								arg_values = inspect.getargspec(cls.__init__).defaults
							except ValueError:
								constructor = inspect.signature(cls.__init__)
								parameters = constructor.parameters
								arg_values = [parameter.default for parameter in parameters.values() if parameter.default != inspect.Parameter.empty]
							finally:
								index = args_from_stored_constructor_py.index(arg)
								state['args'].update({arg:arg_values[index]})

				### Class redefinition if the class inherite to QuickScope, To_Disk or MessagesCollector

				### find all members that is class
				try:
					module = sys.modules[cls.__name__]
				except KeyError:
					module = inspect.getmodule(cls)
				finally:
					clsmembers = inspect.getmembers(module, inspect.isclass)
					names = [t[0] for t in clsmembers]
				
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
				sys.stderr.write(_("Error in setstate for CodeBlock class which is %s\n"%str(cls)))

		state['bad_filename_path_flag'] = False
		### if the python path is wrong
		if not os.path.exists(python_path) :#and zipfile.is_zipfile(os.path.dirname(python_path))):
			### if the model path is empty (for pure python file - not .amd or .cmd)
			if model_path == '' :
				path = python_path

				### if DOMAIN is in python_path
				if dir_name in python_path:
					
					### try to find in DOMAIN directory
					path = os.path.join(os.path.dirname(DOMAIN_PATH), relpath(str(python_path[python_path.index(dir_name):]).strip('[]')))

					### try to find it in exportedPathList (after Domain check) and recent opened file
					if not os.path.exists(path) and builtins.__dict__.get('GUI_FLAG',True):
						import wx
						mainW = wx.GetApp().GetTopWindow()
						if hasattr(mainW,'exportPathsList') and hasattr(mainW,'openFileList'):
							for p in mainW.exportPathsList+mainW.openFileList:
								lib_name = os.path.basename(p)
								if lib_name !='' and lib_name in path:
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
					
				### try to find the python_path in recent opened file directory
				if not os.path.exists(path) and builtins.__dict__.get('GUI_FLAG',True):
					import wx
					mainW = wx.GetApp().GetTopWindow()
					if hasattr(mainW,'exportPathsList') and hasattr(mainW,'openFileList'):
						for a in [os.path.dirname(p) for p in mainW.exportPathsList+mainW.openFileList]:
							p = os.path.join(a,os.path.basename(python_path))
							if os.path.exists(p):
								path = p
								break

				### if path is always wrong, flag is visible
				if os.path.exists(path):
					state['python_path'] = path
				else:
					state['bad_filename_path_flag'] = True

			### for .cmd or .amd
			else:
				if not os.path.exists(state['model_path']) :
					state['bad_filename_path_flag'] = True
				# else:
				# 	with zipfile.ZipFile(model_path) as zf:
				# 		### find all python files
				# 		for file in zf.namelist():
				# 			path =  os.path.join(model_path, os.path.basename(model_path).replace('.amd','.py').replace('.cmd','.py'))
				# 			#cls = GetClass(path)
				# 			if file.endswith(".py"):# and (issubclass(cls, DomainBehavior) or issubclass(cls, DomainStructure)):
				# 				if os.path.exists(model_path):
				# 					state['python_path'] = path
				# 				else:
				# 					state['bad_filename_path_flag'] = True
								#state['python_path'] = os.path.join(model_path, os.path.basename(model_path).replace('.amd','.py').replace('.cmd','.py'))
								#state['bad_filename_path_flag'] =  file != state['python_path'] 
		
		### if the fileName attribut dont exist, we define it into the current devsimpy directory (then the user can change it from Property panel)
		### args is loaded before for .amd and .cmd. See Load function to intercept args.
		if 'args' in state: #and model_path == '' :
			
			### find all word containning 'filename' without considering the casse
			m = [re.match('[a-zA-Z]*filename[_-a-zA-Z0-9]*',s, re.IGNORECASE) for s in list(state['args'].keys())]
			filename_list = [a.group(0) for a in [s for s in m if s is not None]]
			### for all filename attr
			for name in filename_list:
				fn = state['args'][name]
				if not os.path.exists(fn):
					#fn_dn = os.path.dirname(fn)
					fn_bn = os.path.basename(relpath(fn))
		
					### try to redefi[ne the path
					### if Domain is in the path
					if dir_name in fn:
						fn = os.path.join(os.path.dirname(DOMAIN_PATH), relpath(str(fn[fn.index(dir_name):]).strip('[]')))
					### try to find the filename in the recent opened recent file directory or exported lib diretory
					else:
						### for no-gui compatibility
						if builtins.__dict__.get('GUI_FLAG',True):
							import wx
							mainW = wx.GetApp().GetTopWindow()
							if hasattr(mainW,'exportPathsList') and hasattr(mainW,'openFileList'):
								for a in [os.path.dirname(p) for p in mainW.exportPathsList+mainW.openFileList]:
									path = os.path.join(a,fn_bn)
									if os.path.exists(path):
										fn = path
										break

					### show flag icon on the block only for the file with extension (input file)
					if not os.path.exists(fn) and os.path.splitext(fn)[-1] != '':
						state['bad_filename_path_flag'] = True

					state['args'][name] = fn

		####################################" Just for old model
		if 'bad_filename_path_flag' not in state: state['bad_filename_path_flag'] = False
		if 'lock_flag' not in state: state['lock_flag'] = False
		if 'image_path' not in state:
			state['image_path'] = ""
			state['attributes'].insert(3,'image_path')
		if 'font' not in state: state['font'] = [FONT_SIZE, 74, 93, 700, u'Arial']
		if 'font' not in state['attributes']: state['attributes'].insert(3,'font')
		if 'selected' not in state: state['selected'] = False
		if 'label_pos' not in state: state['label_pos'] = 'center'
		if 'input_direction' not in state: state['input_direction'] = 'ouest'
		if 'output_direction' not in state: state['output_direction'] = 'est'
		if '_input_labels' not in state: state['_input_labels'] = {}
		if '_output_labels' not in state: state['_output_labels'] = {}
 		##############################################

		self.__dict__.update(state)
		if new_class:
			self.__class__ = new_class

	###
	def __getstate__(self):
		"""Return state values to be pickled."""
		return Achievable.__getstate__(self)

	###
	def __getattr__(self, name):
		"""Called when an attribute lookup has not found the attribute in the usual places
		"""
		if name == 'dump_attributes':
			#return ['model_path', 'python_path', 'args'] + self.GetAttributes()
			return ['args'] + Connectable.DUMP_ATTR + self.GetAttributes()
		#=======================================================================
		elif name == 'dump_abstr_attributes':
			### Atomic model has no abstract attributes
			return []
		#======================================================================
		else:
			raise AttributeError(name)

	def draw(self, dc):
		"""
		"""
		if self.selected:
			### inform about the nature of the block using icon
			name = 'atomic3.png' if self.model_path != "" else 'pythonFile.png' if self.python_path.endswith('.py') else 'pyc.png' 
			img = wx.Bitmap(os.path.join(ICON_PATH_16_16, name), wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap(img, int(self.x[1]-20), int(self.y[0]))

		Block.draw(self, dc)

	###
	def OnLeftDClick(self, event):
		""" On left double click event has been invoked.
		"""
		if event.ControlDown():
			Selectable.OnRenameFromClick(self, event)
		else:
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

			### if intersection is total, all bad field are has been edited and we test at the end of the loop if all of the paths are right.
			if len(bad_flag_set.intersection(edited_field_set)) == len(bad_flag_set):
				for prop in state:
					### Update the filename flag
					m = [re.match('[a-zA-Z_]*ilename[_-a-zA-Z0-9]*',prop, re.IGNORECASE)]
					filename_list = [a.group(0) for a in [s for s in m if s is not None]]
					### for all filename attr
					for name in filename_list:
						val = state[prop]
						# if behavioral propertie
						if prop in self.args:
							### is abs fileName ?
							if os.path.isabs(val):
								### if there is an extention, then if the field path exist we color in red and update the bad_filename_path_flag
								bad_flag_dico.update({prop:not os.path.exists(val) and os.path.splitext(val)[-1] == ''})
				
				self.bad_filename_path_flag = True in list(bad_flag_dico.values())

	###
	def __repr__(self):
		""" Text representation.
		"""
		return "".join([Block.__repr__(self),
						_("\t DEVS module path: %s\n")%str(self.python_path),
						_("\t DEVSimPy model path: %s\n")%str(self.model_path),
						_("\t DEVSimPy image path: %s\n")%str(self.image_path)]
					)	

#---------------------------------------------------------
class ContainerBlock(Block, Diagram):
	""" ContainerBlock(label, inputs, outputs)
	"""

	FILL = [GREEN]
	
	###
	def __init__(self, label = 'ContainerBlock', nb_inputs = 1, nb_outputs = 1):
		""" Constructor
		"""
		Block.__init__(self, label, nb_inputs, nb_outputs)
		Diagram.__init__(self)

		self.fill = ContainerBlock.FILL

	###
	def __setstate__(self, state):
		""" Restore state from the unpickled state values.
		"""

		python_path = state['python_path']
		model_path = state['model_path']

		dir_name = os.path.basename(DOMAIN_PATH)

		### if the model path is wrong
		if model_path != '':
			if not os.path.exists(model_path):
				### try to find it in the Domain (firstly)
				if dir_name in python_path:

					path = os.path.join(os.path.dirname(DOMAIN_PATH), relpath(str(model_path[model_path.index(dir_name):]).strip('[]')))

					#print(path)
     
					### try to find it in exportedPathList (after Domain check)
					if not os.path.exists(path) and builtins.__dict__.get('GUI_FLAG',True):
						import wx
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

						python_filename = os.path.basename(python_path)

						if str(python_filename).find('\\'):
							### wrong basename :
							### os.path.basename does not work when executed on Unix
							### with a Windows path
							python_path = python_path.replace('\\','/')
							python_filename = os.path.basename(python_path)

						state['python_path'] = os.path.join(state['model_path'] , python_filename)

						if not state['python_path'].endswith('.py'):
							### Is this up-to-date???
							### we find the python file using re module
							### because path can comes from windows and then sep is not the same and os.path.basename don't work !
							state['python_path'] = os.path.join(path, re.findall("([\w]*[%s])*([\w]*.py)"%os.sep, python_path)[0][-1])
				else:
					state['bad_filename_path_flag'] = True

			### load enventual Plugin
			if 'plugins' in state and builtins.__dict__.get('GUI_FLAG',True):
				wx.CallAfter(self.LoadPlugins, (state['model_path']))

			### test if args from construcor in python file stored in library (on disk) and args from stored model in dsp are the same
			if os.path.exists(python_path) or zipfile.is_zipfile(os.path.dirname(python_path)):
				cls = Components.GetClass(state['python_path'])
				if not isinstance(cls, tuple):
					try:
						args_from_stored_constructor_py = inspect.getargspec(cls.__init__).args[1:]
					except:
						constructor = inspect.signature(cls.__init__)
						parameters = constructor.parameters
						args_from_stored_constructor_py = [name for name, _ in parameters.items() if name != 'self']
	    
					args_from_stored_block_model = state['args']
					if args_from_stored_block_model:
						L = list(set(args_from_stored_constructor_py).symmetric_difference( set(args_from_stored_block_model)))
						if L:
							for arg in L:
								if not arg in args_from_stored_constructor_py:
									sys.stdout.write(_("Warning: %s come is old ('%s' arg is deprecated). We update it...\n"%(state['python_path'],arg)))
									del state['args'][arg]
								else:
									try:
										arg_values = inspect.getargspec(cls.__init__).defaults
									except ValueError:
										constructor = inspect.signature(cls.__init__)
										parameters = constructor.parameters
										arg_values = [parameter.default for parameter in parameters.values() if parameter.default != inspect.Parameter.empty]
									finally:
										index = args_from_stored_constructor_py.index(arg)
										state['args'].update({arg:arg_values[index]})
					else:
						#sys.stderr.write(_("args is None in setstate for ContainerBlock: %s\n"%str(cls)))
						state['args'] = {}
				else:
					sys.stderr.write(_("Error in setstate for ContainerBlock: %s\n"%str(cls)))

		### if the model path is empty and the python path is wrong
		elif not (os.path.exists(python_path) and zipfile.is_zipfile(os.path.dirname(python_path))):
			if dir_name in python_path:

				path = os.path.join(os.path.dirname(DOMAIN_PATH), relpath(str(python_path[python_path.index(dir_name):]).strip('[]')))
				state['python_path'] = path

				if not os.path.exists(path):
					state['bad_filename_path_flag'] = True
			else:
				state['bad_filename_path_flag'] = True

		
		####################################" Just for old model
		if 'bad_filename_path_flag' not in state: state['bad_filename_path_flag'] = False
		if 'lock_flag' not in state: state['lock_flag'] = False
		if 'parent' not in state: state['parent'] = None
		if 'image_path' not in state:
			state['image_path'] = ""
			state['attributes'].insert(3,'image_path')
		if 'font' not in state: state['font'] = [FONT_SIZE, 74, 93, 700, u'Arial']
		if 'font' not in state['attributes']: state['attributes'].insert(3,'font')
		if 'selected' not in state: state['selected'] = False
		if 'label_pos' not in state:state['label_pos'] = 'center'
		if 'input_direction' not in state: state['input_direction'] = 'ouest'
		if 'output_direction' not in state: state['output_direction'] = 'est'
		if '_input_labels' not in state: state['_intput_labels'] = {}
		if '_output_labels' not in state: state['_output_labels'] = {}
		#if isinstance(state['shapes'],dict): state['shapes'] = list(state['shapes'].values())
		#####################################
  
		self.__dict__.update(state)

	def __getstate__(self):
		"""Return state values to be pickled."""
		#return Structurable.__getstate__(self)
		return Diagram.__getstate__(self)

	def __getattr__(self, name):
		"""Called when an attribute lookup has not found the attribute in the usual places
		"""

		if name == 'dump_attributes':
			#return ['shapes', 'priority_list', 'constants_dico', 'model_path', 'python_path','args'] + self.GetAttributes()
			return ['shapes', 'priority_list', 'constants_dico','args'] + Connectable.DUMP_ATTR +self.GetAttributes()
		#=======================================================================
		elif name == 'dump_abstr_attributes':
			return Abstractable.DUMP_ATTR if hasattr(self, 'layers') and hasattr(self, 'current_level') else []
		#======================================================================
		else:
			raise AttributeError(name)

	def draw(self, dc):
		"""
		"""
		if self.selected:
			### inform about the nature of the block using icon
			img = wx.Bitmap(os.path.join(ICON_PATH_16_16, 'coupled3.png'), wx.BITMAP_TYPE_ANY)

			### Draw the number of devs models inside
			n = str(self.GetBlockCount())
			dc.DrawText(n, int(self.x[1]-15-len(n)), int(self.y[1]-20))
  
			dc.DrawBitmap(img, int(self.x[1]-20), int(self.y[0]))

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
		### CtrL is Down
		if event.ControlDown():
			Selectable.OnRenameFromClick(self, event)
		else:
			canvas = event.GetEventObject()
			canvas.deselect()

			mainW = wx.GetApp().GetTopWindow()

			frame = DetachedFrame(parent = mainW, title  = ''.join([canvas.name,' - ',self.label]), diagram = self, name = self.label)
			frame.SetIcon(mainW.GetIcon())
			frame.Show()
		
		event.Skip()

	def __repr__(self):
		return "".join([Block.__repr__(self),
					_("\t DEVS module path: %s\n"%str(self.python_path)),
					_("\t DEVSimPy model path: %s\n")%str(self.model_path),
					_("\t DEVSimPy image path: %s\n")%str(self.image_path)]
				)

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

	# def showProperties(self):
	# 	""" Call item properties.
	# 	"""
	# 	self.item.showProperties

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
		
		### Ctrl button is pressed
		if event.ControlDown():
			### change the label of node
			self.OnEditLabel(event)
		else:
			### deselect the block to delete the info flag
			self.cf.deselect(self.item)
		
		event.Skip()

	def OnEditLabel(self, event):
		""" Function called by the OnRightDown call event function.
		"""
		### old label
		old_label = self.label

		### is INode ?
		isINode = isinstance(self, INode)

		### ask tne new label
		d = wx.TextEntryDialog(None, _('New label for the %s port %d:'%("input" if isINode else "output",self.index)), value = old_label, style=wx.OK)

		if d.ShowModal() == wx.ID_OK:
			### new label
			new_label = d.GetValue()

			### only if new and old label are different
			if new_label != old_label:
				self.label = new_label
				if isINode:
					self.item.addInputLabels(self.index, self.label)
				else:
					self.item.addOutputLabels(self.index, self.label)

	def HitTest(self,x,y):
		""" Collision detection method.
		"""

		### old model can produce an error
		try:
			r = self.graphic.r
			xx = self.x[0] if isinstance(self.x, array.array) else self.x
			yy = self.y[0] if isinstance(self.y, array.array) else self.y

			return not ((x < xx-r or x > xx+r) or (y < yy-r or y > yy+r))
		except Exception as info:
			sys.stdout.write(_("Error in Hitest for %s : %s\n")%(self,info))
			return False

class INode(ConnectableNode):
	""" INode(item, index, cf)
	"""

	def __init__(self, item, index, cf, label=None):
		""" Constructor.
		"""
		ConnectableNode.__init__(self, item, index, cf)

		self.label = f"in{self.index}" if not label else label

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

	def OnRightDown(self, event):
		""" Left Down click has been invoked.
		"""
		### dialog to ask new port label
		
		menu = Menu.NodePopupMenu(self)
		### Show popup_menu
		canvas = event.GetEventObject()
		canvas.PopupMenu(menu, event.GetPosition())
		### destroy menu local variable
		menu.Destroy()
		
		event.Skip()

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

		self.fill = [GREEN]

		dc.SetFont(wx.Font(10, 70, 0, 400))

		### prot number
		#dc.SetPen(wx.Pen(wx.NamedColour('black'), 20))
		#dc.DrawText(str(self.index), self.x-self.graphic.r, self.y-self.graphic.r-2)

		### position of label - not for Port model (inside containerBlock)
		if not isinstance(self.item, Port):
			### prepare label position
			if self.item.input_direction == 'ouest':
				xl = x-self.graphic.r-8*len(self.label)
				yl = y-8
			elif self.item.input_direction == 'est':
				xl = x+6
				yl = y-8
			elif self.item.input_direction == 'nord':
				xl = x
				yl = y-18
			else:
				xl = x
				yl = y+2

			### Draw label in port
			dc.DrawText(self.label, int(xl), int(yl))

		### Drawing
		PointShape.draw(self, dc)

class ONode(ConnectableNode):
	""" ONode(item, index, cf).
	"""

	def __init__(self, item, index, cf, label=None):
		""" Constructor.
		"""
		ConnectableNode.__init__(self, item, index, cf)

		self.label = "out%d"%self.index if not label else label

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

	def OnRightDown(self, event):
		""" Left Down click has been invoked.
		"""
		### dialog to ask new port label
		
		menu = Menu.NodePopupMenu(self)
		### Show popup_menu
		canvas = event.GetEventObject()
		canvas.PopupMenu(menu, event.GetPosition())
		### destroy menu local variable
		menu.Destroy()
		
		event.Skip()

	def leftUp(self, items):
		""" Left up action has been invocked.
		"""

		cs = items[0]

		#if self.item in cs.touch_list:
			#index = cs.touch_list.index(self.item)
			#del cs.touch_list[index]

		if len(items) == 1 and isinstance(cs, ConnectionShape) and cs.input is None:
			cs.setInput(self.item, self.index)
			#cs.ChangeForm(ShapeCanvas.CONNECTOR_TYPE)

	def draw(self, dc):
		""" Drawing method.
		"""
		x,y = self.item.getPortXY('output', self.index)
		self.moveto(x, y)
		self.fill = [RED]

		dc.SetFont(wx.Font(10, 70, 0, 400))
		#dc.SetPen(wx.Pen(wx.NamedColour('black'), 20))

		### prot number
		#dc.DrawText(str(self.index), self.x-self.graphic.r, self.y-self.graphic.r-2)

		### position of label
		if not isinstance(self.item, Port):
			### perapre label position
			if self.item.output_direction == 'est':
				xl = x+6
				yl = y-8
			elif self.item.output_direction == 'ouest':
				xl = x-self.graphic.r-8*len(self.label)
				yl = y-8
			elif self.item.output_direction == 'nord':
				xl = x
				yl = y-20
			else:
				xl = x
				yl = y-2

			### Draw label above port
			dc.DrawText(self.label, int(xl), int(yl))

		### Drawing
		PointShape.draw(self, dc)

###
class ResizeableNode(Node):
	""" Resizeable(item, index, cf, type).
	"""

	def __init__(self, item, index, cf, t = 'rect'):
		""" Constructor.
		"""
		Node.__init__(self, item, index, cf, t)

		self.fill = [BLACK]

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

		event.Skip()

	def HitTest(self,x,y):
		""" Collision detection method.
		"""
		return self.graphic.HitTest(x,y)

#---------------------------------------------------------
class Port(CircleShape, Connectable, Selectable, Attributable, Rotatable, Observer):
	""" Port(x1, y1, x2, y2, label).
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
		if 'font' not in state: state['font'] = [FONT_SIZE, 74, 93, 700, u'Arial']
		if 'label_pos' not in state:
			state['label_pos'] = 'center'
			state['attributes'].insert(1,'label_pos')
		if 'output_direction' not in state: state['output_direction'] ="est"
		if 'input_direction' not in state: state['input_direction'] = "ouest"
		if '_input_labels' not in state: state['_input_labels'] = {}
		if '_output_labels' not in state: state['_output_labels'] = {}
		##############################################

		self.__dict__.update(state)

	def draw(self, dc):
		""" Drawing method.
		"""

		# Mac's DC is already the same as a GCDC, and it causes
        # problems with the overlay if we try to use an actual
        # wx.GCDC so don't try it.
		if 'wxMac' not in wx.PlatformInfo:
			dc = wx.GCDC(dc)

		CircleShape.draw(self, dc)
		
		w,h = dc.GetTextExtent(self.label)

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

		dc.DrawText(self.label, int(mx), int(my))

		if self.lock_flag:
			img = wx.Bitmap(os.path.join(ICON_PATH_16_16, 'lock.png'),wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap(img, int(self.x[0]+w/3), int(self.y[0]))

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

		event.Skip()

	# ###
	# def OnLeftDown(self, event):
	# 	""" Left down event has been invoked.
	# 	"""
	# 	### Rename the shape with CtrL+LeftDown
	# 	if event.ControlDown():
	# 		Selectable.OnRenameFromClick(self, event)
	# 	event.Skip()

	def OnProperties(self, event):
		""" Properties of port has been invoked.
		"""
		canvas = event.GetEventObject()
		f = AttributeEditor(canvas.GetParent(), wx.NewIdRef(), self, canvas)
		f.Show()

	###
	def OnLeftDClick(self, event):
		""" Left double click event has been invoked.
		"""
		if event.ControlDown():
			Selectable.OnRenameFromClick(self, event)
		else:
			self.OnProperties(event)
		event.Skip()

	def update(self, concret_subject = None):
		""" Update function linked to notify function (observer pattern).
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
		s=_("\t Label: %s\n")%self.label
		return s

#------------------------------------------------------------------
class iPort(Port):
	""" IPort(label) for ContainerBlock (coupled model)
	"""

	def __init__(self, label = 'iPort'):
		""" Constructor.
		"""

		Port.__init__(self, 50, 60, 100, 120, label)
		self.fill= [GREEN]
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
	""" OPort(label) for ContainerBlock (coupled model)
	"""

	def __init__(self, label = 'oPort'):
		""" Construcotr
		"""

		Port.__init__(self, 50, 60, 100, 120, label)
		self.fill = [RED]
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

		self.fill = [ORANGE]

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

		event.Skip()

#------------------------------------------------
class DiskGUI(CodeBlock):
	""" DiskGUI(label)
	"""

	def __init__(self, label='DiskGUI'):
		""" Constructor.
		"""
		CodeBlock.__init__(self, label, 1, 0)

		self.fill = [ORANGE]

	def OnLeftDClick(self, event):
		""" Left Double Click has been appeared.
		"""
		devs = self.getDEVSModel()

		if devs:
			frame= SpreadSheet.Newt( wx.GetApp().GetTopWindow(),
									wx.NewIdRef(),
									_("SpreadSheet %s")%self.label,
									devs,
									devs.comma if hasattr(devs, 'comma') else " ")
			frame.Center()
			frame.Show()
		else:
			CodeBlock.OnLeftDClick(self, event)
		
		event.Skip()
