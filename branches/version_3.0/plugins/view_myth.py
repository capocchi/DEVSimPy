# -*- coding: utf-8 -*-

""" 
	Authors: L. Capocchi (capocchi@univ-corse.fr)
	Date: 29/03/2010
	Description:
		Give a myth view
	Depends:
"""

### ----------------------------------------------------------

### at the beginning to prevent with statement for python vetrsion <= 2.5
from __future__ import with_statement
import os

import wx
import Core.Components.Container as Container

import Core.Utilities.pluginmanager as pluginmanager
import GUI.Editor as Editor


@pluginmanager.register("START_MYTH_VIEW")
def start_myth_viewer(*args, **kwargs):
	""" Start the diagram frame.
	"""

	r = kwargs['lab']

	filename = os.path.join(HOME_PATH, OUT_DIR, "%s.dat" % r)
	### only with python 2.6
	with open(filename, 'r') as f:
		text = f.read()

	editorFrame = Editor.Editor(wx.GetApp().GetTopWindow(), wx.ID_ANY, "Myth", None)
	editorFrame.text.SetValue(text)
	editorFrame.Show()


def Config(parent):
	""" Plugin settings frame.
	"""

	global cb
	global diagram

	main = wx.GetApp().GetTopWindow()
	currentPage = main.nb2.GetCurrentPage()
	diagram = currentPage.diagram

	frame = wx.Frame(parent, wx.ID_ANY, title=_('Myth Viewer'),
					 style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)
	panel = wx.Panel(frame, wx.ID_ANY)

	lst = map(lambda a: a.label, filter(lambda s: "TransformationADEVS" in s.python_path, diagram.GetShapeList()))

	vbox = wx.BoxSizer(wx.VERTICAL)
	hbox = wx.BoxSizer(wx.HORIZONTAL)

	st = wx.StaticText(panel, wx.ID_ANY, _("Select myth viewers:"), (10, 10))
	cb = wx.CheckListBox(panel, wx.ID_ANY, (10, 30), (370, 120), lst)

	selBtn = wx.Button(panel, wx.ID_SELECTALL)
	desBtn = wx.Button(panel, wx.ID_ANY, _('Deselect All'))
	okBtn = wx.Button(panel, wx.ID_OK)

	hbox.Add(selBtn, 0, wx.LEFT)
	hbox.Add(desBtn, 0, wx.CENTER)
	hbox.Add(okBtn, 0, wx.RIGHT)
	vbox.Add(st, 0, wx.ALL, 5)
	vbox.Add(cb, 1, wx.EXPAND, 5)
	vbox.Add(hbox, 0, wx.CENTER)

	panel.SetSizer(vbox)

	### si des modeles sont deja actives pour le plugin il faut les checker
	num = cb.GetCount()
	cb.SetChecked(
		[index for index in range(num) if diagram.GetShapeByLabel(cb.GetString(index)).__class__ == MythViewer])

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
			shape.__class__ = MythViewer if cb.IsChecked(index) else Container.CodeBlock

		frame.Destroy()

	selBtn.Bind(wx.EVT_BUTTON, OnSelectAll)
	desBtn.Bind(wx.EVT_BUTTON, OnDeselectAll)
	okBtn.Bind(wx.EVT_BUTTON, OnOk)

	frame.CenterOnParent(wx.BOTH)
	frame.Show()


def UnConfig():
	""" Reset the plugin effects on the TransformationADEVS model
	"""

	global cb
	global diagram

	main = wx.GetApp().GetTopWindow()
	currentPage = main.nb2.GetCurrentPage()
	diagram = currentPage.diagram

	lst = map(lambda a: a.label, filter(lambda s: "TransformationADEVS" in s.python_path, diagram.GetShapeList()))

	for label in lst:
		shape = diagram.GetShapeByLabel(label)
		shape.__class__ = Container.CodeBlock

#--------------------------------------------------
class MythViewer(Container.CodeBlock):
	""" MythViewer(label) 
	"""

	def __init__(self, label='MythViewer'):
		""" Constructor
		"""

		Container.CodeBlock.__init__(self, label, 1, 0)

	def OnLeftDClick(self, event):
		""" Left Double Click has been appeared.
		"""

		# If the frame is call before the simulation process, the atomicModel is not instanciate (Instanciation delegate to the makeDEVSconnection after the run of the simulation process)
		devs = self.getDEVSModel()

		if devs is not None:
			pluginmanager.trigger_event('START_MYTH_VIEW', lab=self.label)
		else:
			dial = wx.MessageDialog(None, _('No data available \n Go to the simulation process first !'), 'Info', wx.OK)
			dial.ShowModal()