# -*- coding: utf-8 -*-
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DetachedFrame.py ---
#                     --------------------------------
#                        Copyright (c) 2012
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 19/12/12
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

import sys
import os
import wx

if __name__ == '__main__':
	import __builtin__
	sys.path.append(os.path.dirname(os.getcwd()))
	__builtin__.__dict__['GUI_FLAG'] = True
	__builtin__.__dict__['DEVS_DIR_PATH_DICT'] = {'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')}
	__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = 'PyPDEVS'

# import Core.Components.Container as Container
import GUI.Menu as Menu
import Mixins.Printable as Printable


class DetachedFrame(wx.Frame, Printable.Printable):
	""" Detached Frame including a diagram.
	"""

	def __init__(self, parent=None, ID=wx.ID_ANY, title="", diagram=None, name=""):
		""" Constructor.

			@parent : window parent of the frame
			@ID : ID of the frame
			@title : title of the frame
			@diagram : diagram included in the canvas embedded in the frame
			@name : name of the frame
		"""
		from GUI.ShapeCanvas import ShapeCanvas
		### inherite call
		wx.Frame.__init__(self,
						  parent,
						  ID,
						  title,
						  wx.DefaultPosition,
						  wx.Size(600, 400),
						  name=name,
						  style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)

		### local Copy
		self.title = title
		self.parent = parent
		self.diagram = diagram

		### Canvas Stuff -----------------------------------
		self.canvas = ShapeCanvas(self, wx.ID_ANY, name=title, diagram=self.diagram)
		self.canvas.scalex = 1.0
		self.canvas.scaley = 1.0

		self.transparent = wx.ALPHA_OPAQUE

		### ------------------------Diagram parent manager
		try:
			self.canvas.stockUndo = self.diagram.parent.stockUndo
			self.canvas.stockRedo = self.diagram.parent.stockRedo
		except Exception:
			diagram.SetParent(self.canvas)
			self.canvas.stockUndo = []
			self.canvas.stockRedo = []

		### Menu ToolBar
		toolbar = wx.ToolBar(self, wx.ID_ANY, name='tb', style=wx.TB_HORIZONTAL | wx.NO_BORDER)
		toolbar.SetToolBitmapSize((25, 25)) # just for windows

		
		if self.parent:
			self.toggle_list = wx.GetApp().GetTopWindow().toggle_list
		else:
			sys.stdout.write(_('Alone mode for DetachedFrame: Connector buttons are not binded\n'))
			self.toggle_list = [wx.NewId(), wx.NewId(), wx.NewId()]

		self.tools = [toolbar.AddTool(Menu.ID_SAVE, wx.Bitmap(os.path.join(ICON_PATH, 'save.png')), shortHelpString=_('Save File'), longHelpString=_('Save the current diagram'), clientData=self.canvas),
					  toolbar.AddTool(Menu.ID_SAVEAS, wx.Bitmap(os.path.join(ICON_PATH, 'save_as.png')), shortHelpString=_('Save File As'), longHelpString=_('Save the diagram with an another name'), clientData=self.canvas),
					  toolbar.AddTool(wx.ID_UNDO, wx.Bitmap(os.path.join(ICON_PATH, 'undo.png')), shortHelpString=_('Undo'), longHelpString=_('Click to go back, hold to see history'), clientData=self.canvas),
					  toolbar.AddTool(wx.ID_REDO, wx.Bitmap(os.path.join(ICON_PATH, 'redo.png')), shortHelpString=_('Redo'), longHelpString=_('Click to go forward, hold to see history'), clientData=self.canvas),
					  toolbar.AddTool(Menu.ID_ZOOMIN_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH, 'zoom+.png')), shortHelpString=_('Zoom +'), longHelpString=_('Zoom in'), clientData=self.canvas),
					  toolbar.AddTool(Menu.ID_ZOOMOUT_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH, 'zoom-.png')), shortHelpString=_('Zoom -'), longHelpString=_('Zoom out'), clientData=self.canvas),
					  toolbar.AddTool(Menu.ID_UNZOOM_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH, 'no_zoom.png')), shortHelpString=_('AnnuleZoom'), longHelpString=_('Initial view'), clientData=self.canvas),
					  toolbar.AddTool(Menu.ID_PRIORITY_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH, 'priority.png')), shortHelpString=_('Priority'), longHelpString=_('Activation models priority')),
					  toolbar.AddTool(Menu.ID_CHECK_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH, 'check_master.png')), shortHelpString=_('Check'), longHelpString=_('Check all models')),
					  toolbar.AddTool(Menu.ID_SIM_DIAGRAM, wx.Bitmap(os.path.join(ICON_PATH, 'simulation.png')), shortHelpString=_('Simulation'), longHelpString=_('Simulate the diagram')),
					  toolbar.AddTool(self.toggle_list[0], wx.Bitmap(os.path.join(ICON_PATH, 'direct_connector.png')), shortHelpString=_('Direct'), longHelpString=_('Direct connector'), isToggle=True),
					  toolbar.AddTool(self.toggle_list[1], wx.Bitmap(os.path.join(ICON_PATH, 'square_connector.png')), shortHelpString=_('Square'), longHelpString=_('Square connector'), isToggle=True),
					  toolbar.AddTool(self.toggle_list[2], wx.Bitmap(os.path.join(ICON_PATH, 'linear_connector.png')), shortHelpString=_('Linear'), longHelpString=_('Linear connector'), isToggle=True)
		]

		toolbar.EnableTool(wx.ID_UNDO, not self.canvas.stockUndo == [])
		toolbar.EnableTool(wx.ID_REDO, not self.canvas.stockRedo == [])
		toolbar.InsertSeparator(2)
		toolbar.InsertSeparator(5)
		toolbar.InsertSeparator(9)
		toolbar.InsertSeparator(13)
		toolbar.ToggleTool(self.toggle_list[0], 1)
		toolbar.Realize()

		### if Detached frame from block (container or Code)
		### save, save-as and simulation are desabled
		if not isinstance(self.parent, ShapeCanvas):
			toolbar.EnableTool(Menu.ID_SAVE, False)
			toolbar.EnableTool(Menu.ID_SAVEAS, False)
			toolbar.EnableTool(Menu.ID_SIM_DIAGRAM, False)

		### Call Printable constructor
		Printable.Printable.__init__(self, self.canvas)

		### vertical box
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(toolbar, 0, wx.EXPAND, border=5)
		vbox.Add(self.canvas, 1, wx.EXPAND, border=5)

		self.SetSizer(vbox)

		self.CenterOnParent()

		self.statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP)
		self.statusbar.SetFieldsCount(3)
		self.statusbar.SetStatusWidths([-5, -2, -1])

		self.__binding()

	def __binding(self):
		""" Binding event.
				ClOSE event, IDLE event and MOVE event are binding here.
				All other event are binding in the main application thanks to general identifiers
				NB: ID are defined on the Menu.py file
		"""
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		### Transparent managment when the frame is moving
		self.Bind(wx.EVT_IDLE, self.OnIdle)
		self.Bind(wx.EVT_MOVE, self.OnMove)
		
		### TODO: refactor the devsimpy.py in order to extract OnSaveFile and all of the methods needed here.
		#if not self.parent:
			#self.Bind(wx.EVT_TOOL, parent.OnSaveFile, id=Menu.ID_SAVE)

	def OnMove(self, event):
		""" alpha manager
		"""
		if self.transparent == wx.ALPHA_OPAQUE:
			self.transparent = 140
			try:
				self.SetTransparent(self.transparent)
			except:
				sys.stdout.write(_("No transparency"))
		event.Skip()

	def OnIdle(self, event):
		""" alpha manager
		"""
		if self.transparent == 140:
			self.transparent = wx.ALPHA_OPAQUE
			try:
				self.SetTransparent(self.transparent)
			except:
				sys.stderr.write(_("No transparency"))
		event.Skip()

	def GetCanvas(self):
		""" Return the canvas
		"""
		return self.canvas

	def OnClose(self, event):
		""" Close event has been received.
		"""
		canvas = self.GetCanvas()
		canvas.Refresh()
		### Destroy the windows
		self.Destroy()


### ------------------------------------------------------------


class TestApp(wx.App):
	""" Testing application
	"""

	def OnInit(self):

		import gettext
		import Core.Components.Container as Container
		import __builtin__

		#__builtin__.__dict__['PYDEVS_SIM_STRATEGY_DICT'] = {'original':'SimStrategy1', 'bag-based':'SimStrategy2', 'direct-coupling':'SimStrategy3'}
		#__builtin__.__dict__['PYPDEVS_SIM_STRATEGY_DICT'] = {'original':'SimStrategy4', 'distribued':'SimStrategy5', 'parallel':'SimStrategy6'}

		__builtin__.__dict__['NB_HISTORY_UNDO'] = 5
		__builtin__.__dict__['ICON_PATH'] = os.path.join('Assets','icons')
		__builtin__.__dict__['ICON_PATH_16_16'] = os.path.join(ICON_PATH,'16x16')
		__builtin__.__dict__['_'] = gettext.gettext

		diagram = Container.Diagram()

		self.frame = DetachedFrame(None, -1, "Test", diagram)
		self.frame.Show()
		return True

	def OnQuit(self, event):
		self.Close()

if __name__ == '__main__':

	app = TestApp(0)
	app.MainLoop()