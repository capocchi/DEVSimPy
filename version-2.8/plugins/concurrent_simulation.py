# -*- coding: utf-8 -*-

""" 
	Authors: L. Capocchi (capocchi@univ-corse.fr), S. Toma (toma@univ-corse.fr)
	Date: 12/12/2012
	Description:
		
	Depends: 
"""

### ----------------------------------------------------------

### at the beginning to prevent with statement for python vetrsion <=2.5
from __future__ import with_statement

import sys
import wx
import wx.grid
import os
from wx import xrc
import copy


import inspect

import pluginmanager
import Components

from Container import Block, CodeBlock, ContainerBlock
from DEVSKernel.DEVS import AtomicDEVS, CoupledDEVS
#from plugins.CCSFrame import SimManagerGUI,SimConfigGUI

######################################################################
###						Function Definition
######################################################################
__res = None

def Config(parent):
	""" Plugin settings frame.
	"""

	main = wx.GetApp().GetTopWindow()
	currentPage = main.nb2.GetCurrentPage()
	diagram = currentPage.diagram
	
	#xrcResource = xrc.XmlResource("plugins/CCSFrame.xrc")
	frame = MainFramexrc(parent,diagram)
	#frame = MainFrame(parent, wx.ID_ANY, title = _('Concurent Model Manager'),size= wx.Size( 622,400 ),style = wx.CLOSE_BOX|wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)
	
	frame.SetDiagram(diagram)
	frame.SetLeftListCtrl()
	frame.SetRightCheckListCtrl()
	frame.SetProperties()
	frame.Show()

def get_resources():
    """ This function provides access to the XML resources in this module."""
    global __res
    if __res == None:
        __init_resources()
    return __res

def __init_resources():
	global __res
	__res = xrc.EmptyXmlResource()
	__res.Load(os.path.join('plugins','CCSFrame.xrc'))

@pluginmanager.register("START_CONCURRENT_SIMULATION")
def start_concurrent_simulation(*args, **kwargs):
	""" Start the councurrent simulation decoration
	"""
	
	master = kwargs['master']
	parent = kwargs['parent']
	
	s = SingletonData()
	main = wx.GetApp().GetTopWindow()
	currentPage = main.nb2.GetCurrentPage()
	diagram = currentPage.diagram
	s.SetDefault(diagram)
	
	for devs in GetFlatDEVSList(master, []):
		### TODO to move in decorator
		label = devs.blockModel.label
		block = devs.getBlockModel()
		#lst =s.plugin_act_list
		if hasattr(block,'concFuncList'):
			devs.simData = SingletonData()
			for func in block.concFuncList:
				devs = concurrent_decorator(devs, func)

def decorator(func):
	def wrapped(*args, **kwargs):
		
		try:
			#print "Entering: [%s] with parameters %s" % (func.__name__, args)
				
			devs = func.im_self
			r =  func(*args, **kwargs)	
			devs.concTransition()
			return r
			
		finally:
			pass
			#print "Exiting: [%s]" % func.__name__
	return wrapped

def concurrent_decorator(devs,func='extTransition'):
	''' Decorator for the track of the activity of all atomic model transition function.
	'''
	if func == 'extTransition':
		devs.extTransition = decorator(devs.extTransition)
		#print 'decorate extTransition'
	elif func == 'intTransition':
		devs.intTransition = decorator(devs.intTransition)
		#print 'decorate intTransition'
	elif func == 'outputFnc':
		devs.outputFnc = decorator(devs.outputFnc)
		#print 'decorate outputFnc'

	return devs

def GetFlatDEVSList(coupled_devs, l=[]):
	""" Get the flat list of devs model composing coupled_devs (recursively)
	"""
	for devs in coupled_devs.componentSet:
		if isinstance(devs, AtomicDEVS):
			l.append(devs)
		elif isinstance(devs, CoupledDEVS):
			l.append(devs)
			GetFlatDEVSList(devs,l)
	return l
		
def GetFlatShapesList(diagram,L):
	""" Get the list of shapes recursively
	"""
	for m in diagram.GetShapeList():
		if isinstance(m, CodeBlock):
			L.append(m.label)
		elif isinstance(m, ContainerBlock):
			GetFlatShapesList(m,L)
	return L
	
def GetFlatShapesListConc(diagram, l=[]):
	""" Get the list of shapes with 'concTransition' recursively
	"""
	
	l = GetFlatShapesList(diagram,l)
	lst = []
	for m in map(diagram.GetShapeByLabel,l):
		cls = Components.GetClass(m.python_path)
		boundedMethodList = map(lambda a: a[0], inspect.getmembers(cls, predicate=inspect.ismethod))
		
		if 'concTransition' in boundedMethodList:
			lst.append(m)
			
	return lst
	
	
"""	######################################################################
	###						Class Definition
"""	######################################################################

class Singleton(type):
	""" just add __metaclass__ = Singleton to use it
	"""
	def __init__(self, *args, **kwargs):
		super(Singleton, self).__init__(*args, **kwargs)
		self.__instance = None
	def __call__(self, *args, **kwargs):
		if self.__instance is None:
			self.__instance = super(Singleton, self).__call__(*args, **kwargs)
		return self.__instance

class SingletonData:
	__metaclass__ = Singleton
	
	def __init__(self):
		self.simDico = {}
		
	def AddSimDefault(self,diagram):
		pass
	
	def RemoveSimDefault(self,diagram):
		pass
	
	def SetDefault(self,diagram,nb=None):
		""" Empty the current Singleton Dic and re-initialize the 
		number of simulations to begin with.
		this number is saved inside the diagram.
		TODO
		Need to find a way to initialize every Simulation alone.
		"""
		self.simDico = {}
		if diagram != None:
			if not hasattr(diagram,"defaultNbSim"):
				setattr(diagram,"defaultNbSim",1)
			if nb != None:
				diagram.defaultNbSim = nb
			
		for i in range(diagram.defaultNbSim):
			self.simDico[i] = {}
	
	def Set(self, data):
		self.simDico = data
	
	def Get(self):
		return self.simDico
		
	def addSim(self, simId, signId, signTrace):
		""" Add/update simulation simId with signature to simDico
		"""
		if simId in self.simDico:
			self.simDico[simId].update({signId: Signature(signTrace)})
		else:
			self.simDico[simId] = {signId: Signature(signTrace)}
	
	def count(self):
		return len(self.simDico)

class Signature(object):
	""" TODO
	"""
	def __init__(self, *args, **kwargs):
		""" TODO
		"""
		
		for key,value in kwargs.items():
			setattr(self, key, value)
		
		for val in args:
			if isinstance(val, dict):
				for k,v in val.items():
					setattr(self, k, v)
			elif isinstance(val, list):
				for c in filter(lambda a: isinstance(a, (tuple,list)), val):
					setattr(self, c[0], c[1])

"""	######################################################################
	###						GUI Class Definition
"""	######################################################################

class ListCtrlLeft(wx.ListCtrl):
	def __init__(self, parent, id, diagram):
		wx.ListCtrl.__init__(self, parent, id, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)
		
		self.parent = parent
		self._diagram = diagram
		
		self.SetName('ListCtrlOnLeft')
		
		self.Populate()
		
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelect)
	
	def Populate(self):
		""" Populate the listCtrl
		"""
		block_lst = GetFlatShapesListConc(self._diagram,[])
		### dict for assosiation between label and block
		self.block_dict = dict(map(lambda a: (a.label,a), block_lst))
		
		self.InsertColumn(0, '')
		for label in self.block_dict:
			self.InsertStringItem(0, label)
			
	def OnSize(self, event):
		size = self.parent.GetSize()
		self.SetColumnWidth(0, size.x-5)
		event.Skip()

	def OnSelect(self, event):
		window = self.parent.GetGrandParent().FindWindowByName('CheckListBoxOnRight')
		index = event.GetIndex()
		label = self.GetItemText(index)
		window.Populate(self.block_dict[label])

	def OnDeSelect(self, event):
		index = event.GetIndex()
		self.SetItemBackgroundColour(index, 'WHITE')

	def OnFocus(self, event):
		self.SetItemBackgroundColour(0, 'red')

class CheckListBoxRight(wx.CheckListBox):

	def __init__(self, parent, id, diagram):
		wx.CheckListBox.__init__(self, parent, id, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)

		self.SetName('CheckListBoxOnRight')
		
		self.parent = parent
		self._diagram = diagram
		
		self.Bind(wx.EVT_CHECKLISTBOX, self.EvtCheckListBox)
		
	def Populate(self, block):
		
		self.Clear()
		self.parent_Selection = block.label
		articles = ['extTransition', 'intTransition']
		
		for i in range(len(articles)):
			self.Insert(articles[i],0)

		if not hasattr(block,'concFuncList'):
			setattr(block,'concFuncList',['extTransition'])
		self.SetCheckedStrings(block.concFuncList)
		
	def EvtCheckListBox(self, event):
		
		index = event.GetSelection()
		label = self.GetString(index)
		
		block=self._diagram.GetShapeByLabel(self.parent_Selection)
		if self.IsChecked(index):
			block.concFuncList.append(label)
		else:
			block.concFuncList.remove(label)
			
		self.SetSelection(index)

class MainFramexrc(wx.Frame):
	"""	Main frame for CCS Manager
		loading from xrc file directly using classes Frame and EvtHandler.
	"""
	_diagram = None
	def PreCreate(self, pre):
		""" This function is called during the class's initialization.
		
		Override it for custom setup before the window is created usually to
		set additional window styles using SetWindowStyle() and SetExtraStyle().
		"""
		pass
	
	def __init__(self,parent,diagram=None):
		_xrcName = "SimManagerGUI"
		self._diagram = diagram
		pre = wx.PreFrame()
		self.PreCreate(pre)
		get_resources().LoadOnFrame(pre, parent, _xrcName)
		self.PostCreate(pre)
		
		self.XrcResourceLoadAll()
		self.EventBinding()
		self.SetProperties()
		#self.InitConfigPanel()
		
	def EventBinding(self):
		""" Event Binding
		"""		
		self.DeleteBtn.Bind(wx.EVT_BUTTON, self.OnPushDeleteBtn)
		self.AddBtn.Bind(wx.EVT_BUTTON, self.OnPushAddBtn)
		self.RefreshBtn.Bind(wx.EVT_BUTTON, self.PopulateSimList)
		self.SimSpinCtrl.Bind(wx.EVT_TEXT,self.onSpinChange)
		self.SimList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.ConfigPanelChange)
	
	def XrcResourceLoadAll(self):
		"""Loading Resource from XRC file
		"""
		self.ConcModelPanel =xrc.XRCCTRL(self,"ConcModelPanel")
		self.AssociationFuncPanel = xrc.XRCCTRL(self,"AssociationFuncPanel")
		self.SimConfigPanel = xrc.XRCCTRL(self,"SimConfigPanel")
		self.SimSpinCtrl = xrc.XRCCTRL(self,"SimSpinCtrl")
		self.SimList = xrc.XRCCTRL(self,"SimList")
		self.DeleteBtn = xrc.XRCCTRL(self,"DeleteBtn")
		self.AddBtn = xrc.XRCCTRL(self,"AddBtn")
		self.RefreshBtn = xrc.XRCCTRL(self,"RefreshBtn")
		#pass
	
	### Interface assembling and configuration
	
	def SetLeftListCtrl(self):
		"""Sets the list of Models able to have a CC behavior
		"""
		bsizer = wx.BoxSizer(wx.VERTICAL)
		llst = ListCtrlLeft(self.ConcModelPanel, -1, self._diagram)
		bsizer.Add(llst, 1, wx.EXPAND, 0)
		self.ConcModelPanel.SetSizer(bsizer)
		self.ConcModelPanel.Layout()
		bsizer.Fit(self.ConcModelPanel)

	def SetRightCheckListCtrl(self):
		"""Sets the list of Function that can be executed befor the 
		ConcTransition.
		"""
		bsizer = wx.BoxSizer(wx.VERTICAL)
		rlst = CheckListBoxRight(self.AssociationFuncPanel, -1, self._diagram)
		bsizer.Add(rlst, 1, wx.EXPAND, 0)
		self.AssociationFuncPanel.SetSizer(bsizer)
		self.AssociationFuncPanel.Layout()
		bsizer.Fit(self.AssociationFuncPanel)
		
		#self.bsAssociatedFunc.Add(rlst, 1, wx.EXPAND, 0)

	def SetProperties(self):
		"""Sets the Simulatin list and the interface for the properties of the
		simulation.
		"""
		if not hasattr(self._diagram,"defaultNbSim"):
				setattr(self._diagram,"defaultNbSim",1)
		self.SimSpinCtrl.SetValue(self._diagram.defaultNbSim)
		self.PopulateSimList()
		
		###TODO Add the Populate of the list and add the binding to the
		###		Populate Properties.
		
	def PopulateSimList(self,evt=None):
		s = SingletonData() 
		self.SimList.ClearAll()
		self.SimList.InsertColumn(0, 'Simualtion ID')
		for i in s.simDico:
			self.SimList.InsertStringItem(i,str(i))
		self.SimList.Refresh()
		#pass
	
	def SetDiagram(self, dia=None):
		""" diagram property Setter
		"""
		self._diagram = dia

	### Event Handlers
	def OnPushDeleteBtn(self,evt):
		""" Deletes last simualtion by default, or the selected simualtion
		"""
		###TODO
		item = self.SimList.GetFocusedItem()
		selected = self.SimList.IsSelected(item)
		s = SingletonData()

		if selected == True:
			index = int(self.SimList.GetItemText(item))
			try:
				del s.simDico[index]
			except:
				print "coudn't delete simulation",index,type(index)
		else:
			try:
				key = max(s.simDico.keys())
				del s.simDico[key]
			except:
				print "No Sim to delete"
		
		self.PopulateSimList()
		
	def OnPushAddBtn(self,evt):
		""" Copies last simualtion by default, or the selected simualtion
		"""
		s = SingletonData()
		if s.count() >0:
			key = max(s.simDico.keys())
			sim = copy.deepcopy(s.simDico[key])
			
			####TODO
			#### Add the panel to change the config. and not 
			for d in sim:
				try:
					sim[d].N = sim[d].N+0.1
				except:
					pass
			####
			s.simDico[key+1] = sim
			self.PopulateSimList()

	def onSpinChange(self,evt):
		""" Changes the number of simulation to start with in a CCS.
		"""
		self._diagram.defaultNbSim = self.SimSpinCtrl.GetValue()
	
	def ConfigPanelChange(self,evt):
		###TODO
		###
		#print evt.GetIndex(),evt.GetInt(),evt.GetLabel(),evt.GetPosition(),evt.GetSelection(),evt.GetString(),evt.GetText()
		#self.ConfigPanel.LoadConfig(int(evt.GetLabel()))
		#sizer = self.SimConfigPanel.GetSizer()
		#sizer.Clear()
		sizer = wx.BoxSizer( wx.VERTICAL )
		l = evt.GetLabel()
		if l != None:
			s = SingletonData()
			sim = s.simDico[int(l)]
			i=0
			for d in sim:
				try:
					N = sim[d].N
					sizerLayer = self.AddSimConfigSizer(self.SimConfigPanel,sim,d)
					sizer.Add(sizerLayer,0, wx.EXPAND|wx.ALL, 0 )
					Line = wx.StaticLine(self.SimConfigPanel)
					sizer.Add(Line,0, wx.EXPAND|wx.ALL, 0 )
					
				except:
					print "No Config. to change in this layer"
		else:
			pass
		self.SimConfigPanel.SetSizer(sizer)
		#self.SimConfigPanel.Layout()
		sizer.Fit(self.SimConfigPanel)
			
	def AddSimConfigSizer(self,parent,sim,Id):
		Sizer = wx.GridBagSizer(1,6)
		
		TextN = wx.StaticText( parent, wx.ID_ANY, u"N =", wx.DefaultPosition, wx.DefaultSize, 0 )
		N = wx.TextCtrl( parent, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		N.SetValue(str(sim[Id].N))
		
		TextM = wx.StaticText( parent, wx.ID_ANY, u"M =", wx.DefaultPosition, wx.DefaultSize, 0 )
		M = wx.TextCtrl( parent, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		M.SetValue(str(sim[Id].M))
		
		TextFunc = wx.StaticText( parent, wx.ID_ANY, u"Activation Function = ", wx.DefaultPosition, wx.DefaultSize, 0 )
		m_choice1Choices = ["Sigmoid","tanh"]
		self.m_choice1 = wx.Choice( parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice1Choices, 0 )
		self.m_choice1.SetSelection( 0 )
		#self.m_choice1.SetStringSelection(sim[Id].activation)
		
		#Line = wx.StaticLine(parent, wx.ID_ANY,wx.Li_HORIZONTAL)

		Sizer.Add(TextN,pos=(0, 0), flag=wx.LEFT)
		Sizer.Add(N,pos=(0, 1), flag=wx.LEFT)
		Sizer.Add(TextM,pos=(0, 2), flag=wx.LEFT)
		Sizer.Add(M,pos=(0, 3), flag=wx.LEFT)
		
		Sizer.Add(TextFunc,pos=(0, 4), flag=wx.LEFT)
		Sizer.Add( self.m_choice1,pos=(0, 5), flag=wx.LEFT)
		#Sizer.Add(Line,6,wx.ALL,6)

		return Sizer


#class MainFrame(SimManagerGUI,MainFramexrc):
	#"""Main frame for CCS Manager
	#"""
	#def __init__(self,*args,**kwds):
		#SimManagerGUI.__init__(self,*args,**kwds)
		#self._diagram = diagram
	

#class ConfigPanel(wx.Panel):
	#def __init__(self,parent,diagram):
		#wx.Panel.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		##pre = wx.PrePanel()
		##self.PreCreate(pre)
		##get_resources().LoadOnPanel(pre,parent,_xrcName)
		##self.ConfigPanel =xrc.XRCCTRL(parent,"SimConfigPanel")
		##self.PostCreate(pre)
		
		#self._diagram = diagram
	
	#def LoadConfig(self,Id):
		#bSizerMain = wx.BoxSizer( wx.VERTICAL )
		#if Id != None:
			#s = SingletonData()
			#sim = s.simDico[Id]
			##bSizerMain = wx.BoxSizer( wx.VERTICAL )
			#for d in sim:
				#try:
					#N = sim[d].N
					#sizer = self.AddSizer(sim,d)
					#bSizerMain.Add(sizer,0, wx.EXPAND, 5 )
				#except:
					#print "No Config. to change in this layer"
			##self.SetSizer(bSizerMain)
			#self.SetSizer(bSizerMain)
			#self.Layout()
		#else:
			#pass
	
	#def AddSizer(self,sim,Id):
		#Sizer = wx.BoxSizer( wx.HORIZONTAL )
		
		#TextN = wx.StaticText( self, wx.ID_ANY, u"N = ", wx.DefaultPosition, wx.DefaultSize, 1 )
		#N = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		#N.SetValue(str(sim[Id].N))
		
		#Sizer.Add(TextN,1, wx.ALL, 5)
		#Sizer.Add(N,2,wx.ALL,5)
		
		##TextM = wx.StaticText( self, wx.ID_ANY, u"M = ", wx.DefaultPosition, wx.DefaultSize, 0 )
		##M = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		##M.SetValue(sim[Id].M)
		
		##Sizer.Add(TextN,0, wx.ALL, 5)
		##Sizer.Add(N,0,wx.ALL,5)
		
		##Textf = wx.StaticText( self, wx.ID_ANY, u"Transfer Function = ", wx.DefaultPosition, wx.DefaultSize, 0 )
		
		#return Sizer
		