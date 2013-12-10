# -*- coding: utf-8 -*-

"""
	Authors: L. Capocchi (capocchi@univ-corse.fr),
			J.F. Santucci (santucci@univ-corse.fr)
	Date: 12/09/2013
	Description:
		Activity tracking for DEVSimPy
		We add dynamically a 'activity' attribute to the Block at the GUI level and 'texec'
		(which is dico like {'fnc':[(t1,t1'),(t2,t2'),..]}
		where fnct is the selected transition function, t the simulation time
		(or number of event) and t' the execution yime of fcnt.)
		attribute at the DEVS level. We deduct the tsim doing the sum of texec.
	Depends: 'python-psutil' for cpu usage, networkx and pylab for graph
"""

### ----------------------------------------------------------

### at the beginning to prevent with statement for python vetrsion <=2.5
from __future__ import with_statement

import sys
import wx
import wx.grid
import os
import inspect
import tempfile
import textwrap
import csv

# to send event
if wx.VERSION_STRING < '2.9':
	from wx.lib.pubsub import Publisher as pub
else:
	from wx.lib.pubsub import setuparg1
	from wx.lib.pubsub import pub

#for ploting
try:
	import pydot
except ImportError, info:
	platform_sys = os.name
	if platform_sys in ('nt', 'mac'):
		msg = _("ERROR: pydot module not found.\nhttp://code.google.com/p/pydot/\n")
		sys.stderr.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)
	elif platform_sys == 'posix':
		msg = _("ERROR: pydot module not found.\nPlease install the python-pydot package.\n")
		sys.stderr.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)
	else:
		msg = _("Unknown operating system.\n")
		sys.stdout.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)

#for ploting
try:
	import pylab
except ImportError, info:
	platform_sys = os.name
	if platform_sys in ('nt', 'mac'):
		msg = _("ERROR: Matplotlib module not found.\nhttp://sourceforge.net/projects/matplotlib/files/\n")
		sys.stderr.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)
	elif platform_sys == 'posix':
		msg = _("ERROR: Matplotlib module not found.\nPlease install the python-matplotlib package.\n")
		sys.stderr.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)
	else:
		msg = _("Unknown operating system.\n")
		sys.stdout.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)

# for graph
try:
	import networkx as nx
except ImportError, info:
	platform_sys = os.name
	if platform_sys in ('nt', 'mac'):
		msg = _("ERROR: Networkx module not found.\nhttp://networkx.lanl.gov/download/networkx/\n")
		sys.stderr.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)
	elif platform_sys == 'posix':
		msg = _("ERROR: Networkx module not found.\nPlease install the python-networkx package.\n")
		sys.stderr.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)
	else:
		msg = _("Unknown operating system.\n")
		sys.stdout.write(msg)
		raise ImportError, "%s\n%s"%(msg,info)

### try to import psutil module if is installed.
try:
	from psutil import cpu_times
	def time():
		#User CPU time is time spent on the processor running your program's code (or code in libraries);
		#system CPU time is the time spent running code in the operating system kernel on behalf of your program.
		return cpu_times().user
except ImportError:
	sys.stdout.write('Install psutil module for better cpu result of the plugin.\n The time module has been imported pending.')
	from time import time

import pluginmanager
from Container import Block, CodeBlock, ContainerBlock
from DomainInterface import DomainBehavior, DomainStructure
from PlotGUI import PlotManager

#import profilehooks
#from tempfile import gettempdir

import plugins.codepaths as codepaths

WRITE_DOT_TMP_FILE = False
WRITE_DYNAMIC_METRICS = False

#def profile(func):
	#def wrapped(*args, **kwargs):
		#m = func.im_self
		#f = profilehooks.coverage(fn=func,filename=os.path.join(gettempdir(),'%s.devsimpy.log'%str(m.getBlockModel().label)),immediate=True)
		#r =  f(*args, **kwargs)
		#return r
	#return wrapped

def log(func):
	def wrapped(*args, **kwargs):

		try:
			#print "Entering: [%s] with parameters %s" % (func.__name__, args)
			try:
				### TODO add clock to cpu time consideration
				ts = time()
				r =  func(*args, **kwargs)
				te = time()
				func_name = func.__name__
				devs = func.im_self
				t = te-ts
				ts = devs.timeLast+devs.elapsed

				if not hasattr(devs,'texec'):
					setattr(devs,'texec',{func_name:[(0.0,t)]})
				else:

					if func_name in devs.texec.keys():
						### for number in axis
						#ts = devs.texec[func_name][-1][0]+1
						devs.texec[func_name].append((ts,t))
					else:
						devs.texec[func_name] = [(0.0,t)]

				#print devs, devs.texec,dict(map(lambda k,v: (k,v),devs.texec.keys(), map(lambda a: len(a), devs.texec.values())))
				return r
			except Exception, e:
				sys.stdout.write(_('Exception for Activity-Tracking plugin in %s : %s' % (func.__name__, e)))
		finally:
			pass
			#print "Exiting: [%s]" % func.__name__
	return wrapped

def activity_tracking_decorator(inst):
	''' Decorator for the track of the activity of all atomic model transition function.
	'''
	for name, m in inspect.getmembers(inst, inspect.ismethod):
		if name in inst.getBlockModel().activity.values():
			setattr(inst, name, log(m))
			#setattr(inst,name,profile(m))
	return inst

######################################################################
###				Class Definition
######################################################################

class GenericTable(wx.grid.PyGridTableBase):
	def __init__(self, data, rowLabels=None, colLabels=None):
		wx.grid.PyGridTableBase.__init__(self)
		self.data = data
		self.rowLabels = rowLabels
		self.colLabels = colLabels

	def GetNumberRows(self):
		return len(self.data)

	def GetNumberCols(self):
		return len(self.data[0])

	def GetColLabelValue(self, col):
		if self.colLabels:
			return self.colLabels[col]

	def GetRowLabelValue(self, row):
		if self.rowLabels:
			return self.rowLabels[row]

	def IsEmptyCell(self, row, col):
		return False

	def GetValue(self, row, col):
		return self.data[row][col]

	def SetValue(self, row, col, value):
		pass

class ActivityReport(wx.Frame):
	def __init__(self, parent, id, size, title='', style = wx.DEFAULT_FRAME_STYLE, master=None):
		# begin wxGlade: ActivityReport.__init__
		wx.Frame.__init__(self, parent, id, size=size, title=title, name = 'Tracking', style=style)

		self._title = title
		self._master = master

		self.panel = wx.Panel(self, wx.ID_ANY)

		self.ReportGrid = wx.grid.Grid(self.panel, wx.ID_ANY, size=(1, 1))

		self.timer = wx.Timer(self)

		self.__set_properties()
		self.__do_layout()

		self.timer.Start(2000, oneShot=wx.TIMER_CONTINUOUS)

		self.Bind(wx.EVT_TIMER, self.OnUpdate)
		self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK,self.OnDClick, id=self.ReportGrid.GetId())
		self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK,self.OnRightClick, id=self.ReportGrid.GetId())
		self.ReportGrid.GetGridColLabelWindow().Bind(wx.EVT_MOTION, self.onMouseOverColLabel)
		self.Bind(wx.EVT_BUTTON, self.OnRefresh, id=self.btn.GetId())
		self.Bind(wx.EVT_TOGGLEBUTTON, self.OnDynamicRefresh, id=self.tbtn.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnExport, id=self.ebtn.GetId())

		# end wxGlade

	def __set_properties(self):
		# begin wxGlade: ActivityReport.__set_properties

		self.SetTitle(self._title)

		self.model_list = filter(lambda a: hasattr(a, 'texec'), GetFlatDEVSList(self._master, []))
		self.model_name_list, self.model_id_list = zip(*map(lambda m : (m.getBlockModel().label, m.myID), self.model_list))
		self.mcCabe_list = map(self.GetMacCabe, self.model_list)

		### data used to initialize table
		data = map(lambda a,b,c,d : [a,b,c[0],c[1],c[2],d], self.model_name_list, self.model_id_list, self.GetData(), self.mcCabe_list)

		### MCC stands for McCabe's Cyclomatic Complexity
		colLabels = (_("Model"), _("Id"), _("QActivity"), _("WActivity"), _("CPU (user)"), _('MCC'))
		rowLabels = map(lambda a: str(a), range(len(map(lambda b: b[0], data))))

		tableBase = GenericTable(data, rowLabels, colLabels)

		self.ReportGrid.CreateGrid(10, len(colLabels))
		for i in range(len(colLabels)):
			self.ReportGrid.SetColLabelValue(i, colLabels[i])

		self.ReportGrid.SetTable(tableBase)
		self.ReportGrid.EnableEditing(0)
		self.ReportGrid.AutoSize()

	###
	def __do_layout(self):
		"""
		"""

		sizer_1 = wx.BoxSizer(wx.VERTICAL)
		sizer_2 = wx.BoxSizer(wx.HORIZONTAL)

		self.tbtn = wx.ToggleButton(self.panel,  wx.NewId(), _('Auto-Refresh'))
		self.tbtn.SetValue(True)

		self.btn = wx.Button(self.panel, wx.NewId(), _('Refresh'))
		self.btn.Enable(False)

		self.ebtn = wx.Button(self.panel, wx.NewId(), _('Export'))

		sizer_2.Add(self.tbtn, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3, 3)
		sizer_2.Add(self.btn, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3, 3)
		sizer_2.Add(self.ebtn, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3, 3)

		sizer_1.Add(self.ReportGrid, 1, wx.EXPAND|wx.ALL, 5)
		sizer_1.Add(sizer_2, 0, wx.BOTTOM|wx.EXPAND|wx.ALL, 5)

		self.panel.SetSizer(sizer_1)
		self.Layout()

	def OnExport(self, event):
		"""	csv file exporting
		"""

		wcd = _("CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt|All files (*.*)|*.*")
		home = os.getenv('USERPROFILE') or os.getenv('HOME') or HOME_PATH
		export_dlg = wx.FileDialog(self, message=_('Choose a file'), defaultDir=home, defaultFile='data.csv', wildcard=wcd, style=wx.SAVE|wx.OVERWRITE_PROMPT)
		if export_dlg.ShowModal() == wx.ID_OK:
			fileName = export_dlg.GetPath()
			try:
				spamWriter = csv.writer(open(fileName, 'w'), delimiter=' ', quotechar='|', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
				for row in xrange(self.ReportGrid.GetNumberRows()):
					spamWriter.writerow([self.ReportGrid.GetCellValue(row, i) for i in xrange(self.ReportGrid.GetNumberCols())])

			except Exception, info:
				dlg = wx.MessageDialog(self, _('Error exporting data: %s\n'%info), _('Export Manager'), wx.OK|wx.ICON_ERROR)
				dlg.ShowModal()

			dial = wx.MessageDialog(self, _('Export completed'), _('Export Manager'), wx.OK|wx.ICON_ERROR)
			dial.ShowModal()
			export_dlg.Destroy()

	def OnDynamicRefresh(self, event):
		""" Checkbox has been checked
		"""

		### update the button status
		self.btn.Enable(not self.tbtn.GetValue())

		### update the timer
		if not self.tbtn.GetValue():
			self.timer.Stop()
		else:
			self.timer.Start(2000, oneShot=wx.TIMER_CONTINUOUS)

	def OnRefresh(self, event):
		""" Button Refresh has been pushed
		"""
		if not self.timer.IsRunning():
			self.OnUpdate(event)

	###
	def OnUpdate(self, evt):
		"""
		"""

		table = self.ReportGrid.GetTable()
		data = self.GetData()

		### update table from data
		for i,c in enumerate(data):
			### change value of the cell
			table.SetValue(i, 2, c[0])
			table.SetValue(i, 3, c[1])
			table.SetValue(i, 4, c[2])

			### change the value in the data attribute of the table
			table.data[i][2] = c[0]
			table.data[i][3] = c[1]
			table.data[i][4] = c[2]

			if WRITE_DYNAMIC_METRICS:
				with open(os.path.join(tempfile.gettempdir(),str(table.GetValue(i,0))+"_CPU_.csv"), "a") as file1:
					file1.write(str(c[2])+"\n")

				with open(os.path.join(tempfile.gettempdir(),str(table.GetValue(i,0))+"_QA_.csv"), "a") as file2:
					file2.write(str(c[0])+"\n")

		self.ReportGrid.SetTable(table)
		self.ReportGrid.Refresh()

		#pub().sendMessage(('activity', evt)

	def onMouseOverColLabel(self, event):
		"""
		Displays a tooltip when mousing over certain column labels
		"""
		x = event.GetX()
		y = event.GetY()
		col = self.ReportGrid.XToCol(x, y)

		if col == 0:
			msg = _("Name of model")
		elif col == 1:
			msg = _("Quantitative Activity (A=Aint+Aext)")
		elif col == 2:
			msg = _("Weighted Activity (Zeigler def)")
		elif col == 3:
			msg = _("Time spent on the processor running your program's code")
		elif col == 4:
			msg = _("MacCabe's Cyclomatic Complexity")
		else:
			msg=''

		self.ReportGrid.GetGridColLabelWindow().SetToolTipString(msg)

		event.Skip()

	def showPopupMenu(self, event):
		"""
		Create and display a popup menu on right-click event
		"""

		win  = event.GetEventObject()

		### make a menu
		self.popupmenu = wx.Menu()
		# Show how to put an icon in the menu
		#plot_item = wx.MenuItem(self.popupmenu, wx.NewId(), _("Plot"))
		#table_item = wx.MenuItem(self.popupmenu, wx.NewId(), _("Table"))

		graph_item = wx.MenuItem(self.popupmenu, wx.NewId(), _("Graph"))

		#self.popupmenu.AppendItem(plot_item)
		#self.popupmenu.AppendItem(table_item)

		self.popupmenu.AppendItem(graph_item)

		#self.Bind(wx.EVT_MENU, self.OnPopupItemPlot, plot_item)
		#self.Bind(wx.EVT_MENU, self.OnPopupItemTable, table_item)

		self.Bind(wx.EVT_MENU, self.OnPopupItemGraph, graph_item)

		# Popup the menu.  If an item is selected then its handler
		# will be called before PopupMenu returns.
		win.PopupMenu(self.popupmenu)
		self.popupmenu.Destroy()

	def OnPopupItemPlot(self, event):
		"""
		"""
		#item = self.popupmenu.FindItemById(event.GetId())
        #text = item.GetText()
        pass

	def OnPopupItemGraph(self, event):

		for row in self.ReportGrid.GetSelectedRows():
			label = self.ReportGrid.GetCellValue(row,0)
			id = self.ReportGrid.GetCellValue(row,1)

			### plot the graph
			### TODO link with properties frame
			for fct in ('extTransition','intTransition', 'outputFnc', 'timeAdvance'):
				filename = "%s(%s)_%s.dot"%(label,str(id),fct)
				path = os.path.join(tempfile.gettempdir(), filename)

				### if path exist
				if os.path.exists(path):
					graph = pydot.graph_from_dot_file(path)
					filename_png = os.path.join(tempfile.gettempdir(),"%s(%s)_%s.png"%(label,str(id),fct))
					graph.write_png(filename_png, prog='dot')

					pylab.figure()
					img = pylab.imread(filename_png)
					pylab.imshow(img)

					fig = pylab.gcf()
					fig.canvas.set_window_title(filename)

					pylab.axis('off')
					pylab.show()

					### TODO make analysis to implement probability based on path length
					#nx.draw(g)
					#g = nx.Graph(nx.read_dot(path))
					#distance =nx.all_pairs_shortest_path_length(g)
					#print distance

	def OnPopupItemTable(self, event):
		"""
		"""
		#item = self.popupmenu.FindItemById(event.GetId())
        #text = item.GetText()
		pass

	def OnRightClick(self, evt):
		self.showPopupMenu(evt)

	def OnDClick(self, evt):

		row = evt.GetRow()
		col = evt.GetCol()

		### label of model has been clicked on colon 0 and we plot the quantitative activity
		main = wx.GetApp().GetTopWindow()
		nb2 = main.GetDiagramNotebook()
		currentPage = nb2.GetCurrentPage()
		diagram = currentPage.diagram
		Plot(diagram, self.ReportGrid.GetCellValue(row,0))

	def SetDataToDEVSModel(self, model, quantitative, cpu, weighted):
		""" Embed all information about activity in a new attribute of model (named 'activity')
		"""

		d = {'quantitative' : quantitative, \
			'cpu' : cpu, \
			'weighted' : weighted
			}

		if not hasattr(model, 'activity'):
			setattr(model, 'activity', d)
		else:
			model.activity.update(d)

	def GetMacCabe(self, m):
		"""
		"""

		### Get class of model
		cls = m.__class__

		complexity_int=0.0
		complexity_ext=0.0
		complexity_output=0.0
		complexity_ta=0.0

		### mcCabe complexity
		### beware to use tab for devs code of models

		source_list = map(inspect.getsource, \
						[cls.extTransition, \
						cls.intTransition, \
						cls.outputFnc, \
						cls.timeAdvance])

		for text in source_list:
			### textwrap for deleting the indentation
			ast = codepaths.compiler.parse(textwrap.dedent(text))
			visitor = codepaths.PathGraphingAstVisitor()
			visitor.preorder(ast, visitor)

			for graph in visitor.graphs.values():
				### TODO make this generic
				if 'extTransition' in text:
					complexity_ext += graph.complexity()
					fct = 'extTransition'
				elif 'intTransition' in text:
					complexity_int += graph.complexity()
					fct = 'intTransition'
				elif 'outputFnc' in text:
					complexity_output += graph.complexity()
					fct = 'outputFnc'
				elif 'timeAdvance' in text:
					complexity_ta += graph.complexity()
					fct = 'timeAdvance'
				else:
					pass

				### write dot file
				if WRITE_DOT_TMP_FILE:
					self.worker( m.getBlockModel().label, str(m.myID), fct, str(graph.to_dot()))

		#### TODO make this generic depending on the checked cb2
		complexity = complexity_ext+complexity_int

		return complexity

	def GetData(self):
		"""
		"""

		if self._master:

			quantitative_activity_list = []
			cpu_activity_list = []
			weighted_activity_list = []

			for m in self.model_list:

				quantitative_activity = 0.0
				cpu_activity = 0.0
				weighted_activity = 0.0

				texec_list = m.texec.values()

				for d in texec_list:
					quantitative_activity+=len(d)
					cpu_activity+=sum(map(lambda c: c[-1],d))
					### TODO round for b-a ???
					weighted_activity+=d[-1][0]-d[0][0]

				quantitative_activity_list.append(quantitative_activity)
				cpu_activity_list.append(cpu_activity)
				weighted_activity_list.append(weighted_activity)

				self.SetDataToDEVSModel(m, quantitative_activity, cpu_activity, weighted_activity)

			### A=Aint+Aext/H
			H=self._master.timeLast if self._master.timeLast <= self._master.FINAL_TIME else self._master.FINAL_TIME

			### if models have been simulated during a minimum time H
			if H > 0.0:
				### prepare data to populate grid
				return map(lambda qa, cpu, wa: (qa/H, wa/H, cpu/H), \

							quantitative_activity_list, \
							cpu_activity_list, \
							weighted_activity_list)
			else:
				return False

		else:
			sys.stdout.write(_('Please, go to the simulation process before analyse activity !\n'))
			return False

	def worker(self, label, ID, fct, txt):
		dot_path = os.path.join(tempfile.gettempdir(), "%s(%s)_%s.dot"%(label,str(ID),fct))

		msg = "Starting write %s" % dot_path

		### write file in temp directory
		with open(dot_path,'wb') as f:
			f.write('graph {\n%s}'%txt)

@pluginmanager.register("START_ACTIVITY_TRACKING")
def start_activity_tracking(*args, **kwargs):
	""" Start the definition of the activity attributs for all selected block model
	"""

	master = kwargs['master']
	parent = kwargs['parent']

	for devs in GetFlatDEVSList(master,[]):
		block = devs.getBlockModel()
		if hasattr(block,'activity'):
			devs = activity_tracking_decorator(devs)

@pluginmanager.register("VIEW_ACTIVITY_REPORT")
def view_activity_report(*args, **kwargs):
	""" Start the definition of the activity attributs for all selected block model
	"""

	master = kwargs['master']
	parent = kwargs['parent']

	frame = ActivityReport(parent, wx.ID_ANY, size=(560, 300), title="Activity-Tracking Reporter", master = master)
	frame.Show()

def GetFlatDEVSList(coupled_devs, l=[]):
	""" Get the flat list of devs model composing coupled_devs (recursively)
	"""
	for devs in coupled_devs.componentSet:
		if isinstance(devs, DomainBehavior):
			l.append(devs)
		elif isinstance(devs, DomainStructure):
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

def Plot(diagram, selected_label):

	master = diagram.getDEVSModel()

	if master is not None:

		### for all devs models with texec attribut (activity tracking has been actived for these type of models)
		for m in GetFlatDEVSList(master,[]):
			label = m.getBlockModel().label
			### mdoel is schecked and selected
			if hasattr(m, 'texec') and selected_label == label:
				### add the results attribut specific for quickscope familly models
				setattr(m,'results',m.texec)
				### no fusion because we need to have separate window (if True we have one window)
				setattr(m,'fusion',False)
				### to have getBlockModel attribut, the codeBlock graphical model is introduced
				cb = CodeBlock(label)
				cb.setDEVSModel(m)

				### get canvas from main window
				main = wx.GetApp().GetTopWindow()
				canvas = main.nb2.GetCurrentPage()
				### plot frame has been invoked with a manager (dynamic or static plotting)
				PlotManager(canvas, _("CPU Activity"), m, xl = "Time [s]", yl = "CPU time")

	else:
		dial = wx.MessageDialog(event.GetEventObject(), _('Master DEVS Model is None!\nGo ti the simulation process in order to perform activity tracking.'), _('Plot Manager'), wx.OK | wx.ICON_EXCLAMATION)
		dial.ShowModal()

def Config(parent):
	""" Plugin settings frame.
	"""

	global cb1
	global cb2
	global diagram

	main = wx.GetApp().GetTopWindow()
	nb2 = main.GetDiagramNotebook()
	currentPage = nb2.GetCurrentPage()
	diagram = currentPage.diagram
	master = None

	frame = wx.Frame(parent, wx.ID_ANY, title = _('Activity Tracking'), style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)
	panel = wx.Panel(frame, wx.ID_ANY)

	#lst_1  = map(lambda a: a.label, filter(lambda s: isinstance(s, CodeBlock), diagram.GetShapeList()))
	lst_1 = GetFlatShapesList(diagram,[])
	lst_2  = ('timeAdvance', 'outputFnc', 'extTransition', 'intTransition')

	vbox = wx.BoxSizer(wx.VERTICAL)
	hbox = wx.BoxSizer(wx.HORIZONTAL)
	hbox2 = wx.BoxSizer(wx.HORIZONTAL)

	st = wx.StaticText(panel, wx.ID_ANY, _("Select models and functions to track:"), (10,10))

	cb1 = wx.CheckListBox(panel, wx.ID_ANY, (10, 30), wx.DefaultSize, lst_1, style=wx.LB_SORT)
	cb2 = wx.CheckListBox(panel, wx.ID_ANY, (10, 30), wx.DefaultSize, lst_2)

	selBtn = wx.Button(panel, wx.ID_SELECTALL)
	desBtn = wx.Button(panel, wx.ID_ANY, _('Deselect All'))
	okBtn = wx.Button(panel, wx.ID_OK)
	#reportBtn = wx.Button(panel, wx.ID_ANY, _('Report'))

	hbox2.Add(cb1, 1, wx.EXPAND, 5)
	hbox2.Add(cb2, 1, wx.EXPAND, 5)

	hbox.Add(selBtn, 0, wx.LEFT)
	hbox.Add(desBtn, 0, wx.CENTER)
	hbox.Add(okBtn, 0, wx.RIGHT)

	vbox.Add(st, 0, wx.ALL, 5)
	vbox.Add(hbox2, 1, wx.EXPAND, 5, 5)
	vbox.Add(hbox, 0, wx.CENTER, 10, 10)

	panel.SetSizer(vbox)

	### si des modèles sont deja activés pour le plugin il faut les checker
	num = cb1.GetCount()
	L1=[] ### liste des shapes à checker
	L2={} ### la liste des function tracer (identique pour tous les block pour l'instant)
	for index in range(num):
		block=diagram.GetShapeByLabel(cb1.GetString(index))
		if hasattr(block,'activity'):
			L1.append(index)
			L2[block.label] = block.activity.keys()

	if L1 != []:
		cb1.SetChecked(L1)
		### tout les block on la meme liste de function active pour le trace, donc on prend la première
		cb2.SetChecked(L2.values()[0])

	### ckeck par defaut delta_ext et delta_int
	if L2 == {}:
		cb2.SetChecked([2,3])

	def OnPlot(event):
		''' Bar Plot for the activity tracking performed
		'''

		Plot(diagram, cb1.GetString(cb1.GetSelection()))

	def OnSelectAll(evt):
		""" Select All button has been pressed and all plugins are enabled.
		"""
		cb1.SetChecked(range(cb1.GetCount()))

	def OnDeselectAll(evt):
		""" Deselect All button has been pressed and all plugins are disabled.
		"""
		cb1.SetChecked([])

	def OnOk(evt):
		btn = evt.GetEventObject()
		frame = btn.GetTopLevelParent()
		num1 = cb1.GetCount()
		num2 = cb2.GetCount()

		for index in range(num1):
			label = cb1.GetString(index)

			shape = diagram.GetShapeByLabel(label)
			activity_condition = hasattr(shape,'activity')

			assert(isinstance(shape, Block))

			if cb1.IsChecked(index):
				### dictionnaire avec des clees correspondant aux index de la liste de function de transition et avec des valeurs correspondant aux noms de ces fonctions
				D = dict([(index,cb2.GetString(index)) for index in range(num2) if cb2.IsChecked(index)])
				if not activity_condition:
					setattr(shape, 'activity',D)
				else:
					shape.activity = D
			elif activity_condition:
				del shape.activity


		frame.Destroy()

	selBtn.Bind(wx.EVT_BUTTON, OnSelectAll)
	desBtn.Bind(wx.EVT_BUTTON, OnDeselectAll)
	okBtn.Bind(wx.EVT_BUTTON, OnOk)

	def showPopupMenu(event):
		"""
		Create and display a popup menu on right-click event
		"""

		win  = event.GetEventObject()

		### make a menu
		menu = wx.Menu()
		# Show how to put an icon in the menu
		item = wx.MenuItem(menu, wx.NewId(), "Aext")
		menu.AppendItem(item)
		menu.Append(wx.NewId(), "Aint")
		menu.Append(wx.NewId(), "A=Aext+Aint")

		# Popup the menu.  If an item is selected then its handler
		# will be called before PopupMenu returns.
		win.PopupMenu(menu)
		menu.Destroy()

	def OnRightClickCb1(evt):
		showPopupMenu(evt)

	def OnRightDClickCb1(evt):
		OnPlot(evt)

	### 1. Register source's EVT_s to inOvoke launcher.
	cb1.Bind(wx.EVT_RIGHT_DOWN, OnRightClickCb1)
	cb1.Bind(wx.EVT_LEFT_DCLICK, OnRightDClickCb1)

	frame.CenterOnParent(wx.BOTH)
	frame.Show()

def UnConfig():
	""" Reset the plugin effects on the TransformationADEVS model
	"""

	global cb1
	global cb2
	global diagram

	main = wx.GetApp().GetTopWindow()
	nb2 = main.GetDiagramNotebook()
	currentPage = nb2.GetCurrentPage()
	diagram = currentPage.diagram

	lst  = map(lambda a: a.label, filter(lambda s: isinstance(s, CodeBlock), diagram.GetShapeList()))

	for label in lst:
		shape = diagram.GetShapeByLabel(label)
		if hasattr(shape, 'activity'):
			del shape.activity
