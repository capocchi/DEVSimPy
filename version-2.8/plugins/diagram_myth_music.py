# -*- coding: utf-8 -*-

"""
	Authors: L. Capocchi (capocchi@univ-corse.fr)
	Date: 16/10/2012
	Description:
		Give diagram representation of the DEVS model
	Depends: python-networkx, python-profiler(for gato)
"""

### ----------------------------------------------------------

import sys
import wx
import os

import pluginmanager
from Container import CodeBlock

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

###----------------------------------------------------------------------
def getMythTree(dico, graph):
	for code in dico:
		parent = code
		graph.add_edge(parent, code)
		for elem in dico[code]:
			graph.add_edge(parent, elem)
			parent = elem
	return graph

@pluginmanager.register("START_MYTH_MUSIC_DIAGRAM")
def start_myth_music_diagram(*args, **kwargs):
	""" Start the diagram frame.
	"""

	r = kwargs['fn']
	fn = os.path.join(HOME_PATH,OUT_DIR,r)

	f = open(fn, 'r')

	D = {}
	for line in f.readlines():
		code = line.split(' ')[0]
		L = [line.split(' ')[1],line.split(' ')[2]]
		if D.has_key(code):
			D[code].extend(L)
		else:
			D[code] = L

	G = getMythTree(D, nx.Graph())

	wx.BeginBusyCursor()
	wx.SafeYield()
	### plot the grahp
	#nx.draw(G)
	pylab.show()
	wx.EndBusyCursor()

def Config(parent):
	""" Plugin settings frame.
	"""

	global cb
	global diagram

	main = wx.GetApp().GetTopWindow()
	currentPage = main.nb2.GetCurrentPage()
	diagram = currentPage.diagram

	frame = wx.Frame(parent, wx.ID_ANY, title = _('Myth Music Viewer'), style = wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)
	panel = wx.Panel(frame, wx.ID_ANY)

	vbox = wx.BoxSizer(wx.VERTICAL)
	hbox = wx.BoxSizer(wx.HORIZONTAL)

	lst = map(lambda a: a.label, filter(lambda s: "Observor" in s.python_path, diagram.GetShapeList()))
	st = wx.StaticText(panel, wx.ID_ANY, _("Select myth music viewers:"),(10,10))
	cb = wx.CheckListBox(panel, wx.ID_ANY, (10, 30),(370,120), lst)
	selBtn = wx.Button(panel, wx.ID_SELECTALL)
	desBtn = wx.Button(panel, wx.ID_ANY, _('Deselect All'))
	okBtn = wx.Button(panel, wx.ID_OK)

	hbox.Add(selBtn,0,wx.LEFT)
	hbox.Add(desBtn,0,wx.CENTER)
	hbox.Add(okBtn,0,wx.RIGHT)
	vbox.Add(st, 0, wx.ALL, 5)
	vbox.Add(cb, 1, wx.EXPAND, 5)
	vbox.Add(hbox, 0, wx.CENTER)

	panel.SetSizer(vbox)

	### si des modèles sont deja activés pour le plugin il faut les checker
	num = cb.GetCount()
	cb.SetChecked([index for index in range(num) if diagram.GetShapeByLabel(cb.GetString(index)).__class__ == MythMusicViewer])

	def OnSelectAll(evt):
		""" Select All button has been pressed and all plugins are enabled.
		"""
		cb.SetChecked(range(cb.GetCount()))

	def OnDeselectAll(evt):
		""" Deselect All button has been pressed and all plugins are disabled.
		"""
		cb.SetChecked([])

	def OnOk(evt):
		btn = evt.GetEventObject()
		frame = btn.GetTopLevelParent()
		for index in range(cb.GetCount()):
			label = cb.GetString(index)
			shape = diagram.GetShapeByLabel(label)
			shape.__class__ = MythMusicViewer if cb.IsChecked(index) else CodeBlock

		frame.Destroy()

	selBtn.Bind(wx.EVT_BUTTON, OnSelectAll)
	desBtn.Bind(wx.EVT_BUTTON, OnDeselectAll)
	okBtn.Bind(wx.EVT_BUTTON, OnOk)

	frame.CenterOnParent(wx.BOTH)
	frame.Show()

def UnConfig():
	""" Reset the plugin effects on the Observor model
	"""

	global cb
	global diagram

	main = wx.GetApp().GetTopWindow()
	currentPage = main.nb2.GetCurrentPage()
	diagram = currentPage.diagram

	lst = map(lambda a: a.label, filter(lambda s: "Observor" in s.python_path, diagram.GetShapeList()))

	for label in lst:
		shape = diagram.GetShapeByLabel(label)
		shape.__class__ = CodeBlock

#--------------------------------------------------
class MythMusicViewer(CodeBlock):
	""" MythMusicViewer(label)
	"""

	def __init__(self, label = 'MythMusicViewer'):
		""" Constructor
		"""

		CodeBlock.__init__(self, label, 1, 0)

	def OnLeftDClick(self,event):
		""" Left Double Click has been appeared.
		"""

		# If the frame is call before the simulation process, the atomicModel is not instanciate (Instanciation delegate to the makeDEVSconnection after the run of the simulation process)
		devs = self.getDEVSModel()

		if devs is not None:

			pluginmanager.trigger_event('START_MYTH_MUSIC_DIAGRAM', fn = devs.fileName)
		else:
			dial = wx.MessageDialog(None, _('No data available \n Go to the simulation process first !'), 'Info', wx.OK)
			dial.ShowModal()
