# -*- coding: utf-8 -*-

""" 
	Authors: L. Capocchi (capocchi@univ-corse.fr), S. toma (toma@univ-corse.fr)
	Date: 12/12/2012
	Description:

	Depends:
"""

### ----------------------------------------------------------

### at the beginning to prevent with statement for python vetrsion <= 2.5
from __future__ import with_statement
import sys
import wx
import Core.DEVSKernel.DEVS as DEVS
import Core.Components.Container as Container
# import GUI.PlotGUI as PlotGUI
import Core.Utilities.pluginmanager as pluginmanager


def decorator(func):
	def wrapped(*args, **kwargs):

		try:
			#print "Entering: [%s] with parameters %s" % (func.__name__, args)
			try:
				devs = func.im_self
				r = func(*args, **kwargs)
				devs.concTransition()

				return r
			except Exception, e:
				sys.stdout.write(_('Exception for concurrent simulation plugin in %s : %s' % (func.__name__, e)))
		finally:
			pass
		#print "Exiting: [%s]" % func.__name__

	return wrapped


def concurrent_decorator(inst, func='extTransition'):
	""" Decorator for the track of the activity of all atomic model transition function.
	"""
	if func == 'extTransition':
		inst.extTransition = decorator(inst.extTransition)
	#print 'decorate extTransition'
	elif func == 'intTransition':
		inst.intTransition = decorator(inst.intTransition)
	#print 'decorate intTransition'
	elif func == 'outputFnc':
		inst.outputFnc = decorator(inst.outputFnc)
	#print 'decorate outputFnc'

	return inst

######################################################################
###				Class Definition
######################################################################


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

		for key, value in kwargs.items():
			setattr(self, key, value)

		for val in args:
			if isinstance(val, dict):
				for k, v in val.items():
					setattr(self, k, v)
			elif isinstance(val, list):
				for c in filter(lambda a: isinstance(a, (tuple, list)), val):
					setattr(self, c[0], c[1])


@pluginmanager.register("START_CONCURRENT_SIMULATION")
def start_activity_tracking(*args, **kwargs):
	""" Start the definition of the activity attributs for all selected block model
	"""

	master = kwargs['master']
	parent = kwargs['parent']

	### TODO to change log button using remove from size
	#simDialog = parent
	#log_btn = simDialog._btn4


	#self.Unbind(wx.EVT_PAINT)
	#self.Bind(wx.EVT_BUTTON, toto)

	s = SingletonData()
	#s.Set({})

	for devs in GetFlatDEVSList(master, []):
		### TODO to move in decorator
		label = devs.blockModel.label
		block = devs.getBlockModel()
		#lst = s.plugin_act_list
		if hasattr(block, 'concFuncList'):
			devs.simData = SingletonData()
			try:
				#if label in lst:
				#print block.concFuncList
				for func in block.concFuncList:
					devs = concurrent_decorator(devs, func)
			except:
				devs = concurrent_decorator(devs)

			#s.simDico


def GetFlatDEVSList(coupled_devs, l=None):
	"""
	Get the flat list of devs model composing coupled_devs (recursively)
	"""
	if not l: l = []
	for devs in coupled_devs.componentSet:
		if isinstance(devs, DEVS.AtomicDEVS):
			l.append(devs)
		elif isinstance(devs, DEVS.CoupledDEVS):
			l.append(devs)
			GetFlatDEVSList(devs, l)
	return l


def GetFlatShapesList(diagram, L):
	""" Get the list of shapes recursively
	"""
	for m in diagram.GetShapeList():
		if isinstance(m, Container.CodeBlock):
			L.append(m.label)
		elif isinstance(m, Container.ContainerBlock):
			GetFlatShapesList(m, L)
	return L


def GetFlatShapesListConc(diagram, l=None):
	""" Get the list of shapes with 'concTransition' recursively
	"""
	if not l: l = []

	l = GetFlatShapesList(diagram, l)
	lst = []
	for m in l:
		devsModel = diagram.GetShapeByLabel(m).getDEVSModel()
		if not devsModel is None:
			if hasattr(devsModel, 'concTransition'):
				lst.append(m)
		else:
			lst.append(m)
	return lst


def Config(parent):
	""" Plugin settings frame.
	"""

	global cb1
	global cb2
	global diagram

	main = wx.GetApp().GetTopWindow()
	currentPage = main.nb2.GetCurrentPage()
	diagram = currentPage.diagram
	master = None

	frame = wx.Frame(parent, wx.ID_ANY, title=_('Concurent Simulation'),
					 style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)

	hbox = wx.BoxSizer(wx.HORIZONTAL)
	splitter = wx.SplitterWindow(frame, -1, style=wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)

	vbox1 = wx.BoxSizer(wx.VERTICAL)
	panel1 = wx.Panel(splitter, -1)
	panel11 = wx.Panel(panel1, -1, size=(-1, 40))
	panel11.SetBackgroundColour('#53728c')
	st1 = wx.StaticText(panel11, -1, 'Models', (5, 5))
	st1.SetForegroundColour('WHITE')

	panel12 = wx.Panel(panel1, -1, style=wx.BORDER_SUNKEN)
	vbox = wx.BoxSizer(wx.VERTICAL)
	list1 = ListCtrlLeft(panel12, -1)
	list1.SetName('ListCtrlOnLeft')

	vbox.Add(list1, 1, wx.EXPAND)
	panel12.SetSizer(vbox)
	panel12.SetBackgroundColour('WHITE')

	vbox1.Add(panel11, 0, wx.EXPAND)
	vbox1.Add(panel12, 1, wx.EXPAND)

	panel1.SetSizer(vbox1)

	vbox2 = wx.BoxSizer(wx.VERTICAL)
	panel2 = wx.Panel(splitter, -1)
	panel21 = wx.Panel(panel2, -1, size=(-1, 40), style=wx.NO_BORDER)
	st2 = wx.StaticText(panel21, -1, 'Functions', (5, 5))
	st2.SetForegroundColour('WHITE')

	panel21.SetBackgroundColour('#53728c')
	panel22 = wx.Panel(panel2, -1, style=wx.BORDER_RAISED)
	vbox3 = wx.BoxSizer(wx.VERTICAL)
	list2 = CheckListBoxRight(panel22, -1)
	list2.SetName('CheckListBoxOnRight')
	vbox3.Add(list2, 1, wx.EXPAND)
	panel22.SetSizer(vbox3)

	panel22.SetBackgroundColour('WHITE')
	vbox2.Add(panel21, 0, wx.EXPAND)
	vbox2.Add(panel22, 1, wx.EXPAND)

	panel2.SetSizer(vbox2)

	toolbar = frame.CreateToolBar()
	#toolbar.AddLabelTool(1, 'Exit', wx.Bitmap('Assets/icons/stock_exit.png'))
	toolbar.Realize()

	hbox.Add(splitter, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
	frame.SetSizer(hbox)
	frame.CreateStatusBar()
	splitter.SplitVertically(panel1, panel2)
	frame.CenterOnParent(wx.BOTH)
	frame.Show()


class ListCtrlLeft(wx.ListCtrl):
	def __init__(self, parent, id):
		wx.ListCtrl.__init__(self, parent, id, style=wx.LC_REPORT | wx.LC_HRULES |
													 wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)
		lst_1 = GetFlatShapesListConc(diagram, [])
		self.parent = parent

		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelect)
		self.InsertColumn(0, '')

		for i in range(len(lst_1)):
			self.InsertStringItem(0, lst_1[i])

	def OnSize(self, event):
		size = self.parent.GetSize()
		self.SetColumnWidth(0, size.x - 5)
		event.Skip()

	def OnSelect(self, event):
		window = self.parent.GetGrandParent().FindWindowByName('CheckListBoxOnRight')
		index = event.GetIndex()
		label = self.GetItemText(index)
		window.LoadData(label)

	def OnDeSelect(self, event):
		index = event.GetIndex()
		self.SetItemBackgroundColour(index, 'WHITE')

	def OnFocus(self, event):
		self.SetItemBackgroundColour(0, 'red')


class CheckListBoxRight(wx.CheckListBox):
	def __init__(self, parent, id):
		wx.CheckListBox.__init__(self, parent, id, style=wx.LC_REPORT | wx.LC_HRULES |
														 wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)

		self.parent = parent
		#self.Bind(wx.EVT_LISTBOX, self.EvtListBox)
		self.Bind(wx.EVT_CHECKLISTBOX, self.EvtCheckListBox)

	def LoadData(self, label):
		self.Clear()
		self.parent_Selection = label
		articles = ['timeAdvance', 'outputFnc', 'extTransition', 'intTransition']

		for i in range(len(articles)):
			self.Insert(articles[i], 0)

		block = diagram.GetShapeByLabel(label)

		if not hasattr(block, 'concFuncList'):
			setattr(block, 'concFuncList', ['extTransition'])
		self.SetCheckedStrings(block.concFuncList)

	#def EvtListBox(self, event):
	#print ('EvtListBox: %s\n' % event.GetString())

	def EvtCheckListBox(self, event):
		#simData = SingletonData()

		index = event.GetSelection()
		label = self.GetString(index)

		block = diagram.GetShapeByLabel(self.parent_Selection)
		if self.IsChecked(index):
			block.concFuncList.append(label)
		else:
			block.concFuncList.remove(label)

		self.SetSelection(index)    # so that (un)checking also selects (moves the highlight)
	