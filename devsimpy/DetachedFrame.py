# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DetachedFrame.py ---
#                     --------------------------------
#                        Copyright (c) 2018
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 03/07/18
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
import wx

_ = wx.GetTranslation

wx.ST_SIZEGRIP = wx.STB_SIZEGRIP

import Container
import Menu
import PrintOut
from Utilities import getTopLevelWindow, load_and_resize_image

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# CLASS DEFIINTION
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class DetachedFrame(wx.Frame, PrintOut.Printable):
	""" Detached Frame including a diagram.
	"""

	def __init__(self, parent=None, ID=wx.NewIdRef(), title="", diagram=None, name=""):
		""" Constructor.

			@parent : window parent of the frame
			@ID : ID of the frame
			@title : title of the frame
			@diagram : diagram included in the canvas embedded in the frame
			@name : name of the frame
		"""

		### inherit call
		wx.Frame.__init__(      self,
								parent,
								ID,
								title,
								wx.DefaultPosition,
								wx.Size(600, 450),
								name=name,
								style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN)

		self.default_style = self.GetWindowStyle()

		### local Copy
		self.title = title
		self.parent = parent
		self.diagram = diagram


		### current abstract level
		#=======================================================================
		if hasattr(diagram, 'layers') and hasattr(diagram, 'current_level'):
			level = diagram.layers[0].current_level
			self.diagram = diagram.layers[level]
		else:
			level = 0
			self.diagram = diagram
		#=======================================================================

		### Canvas Stuff -----------------------------------
		self.canvas = Container.ShapeCanvas(self, wx.NewIdRef(), name=title, diagram = self.diagram)
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
		toolbar = wx.ToolBar(self, wx.NewIdRef(), name='tb', style=wx.TB_HORIZONTAL | wx.NO_BORDER)
		toolbar.SetToolBitmapSize((16,16))

		if self.parent:
			self.toggle_list = getTopLevelWindow().toggle_list
		else:
			sys.stdout.write(_('Alone mode for DetachedFrame: Connector buttons are not binded\n'))
			self.toggle_list = [wx.NewIdRef() for i in range(6)]
		
		self.tools = [  toolbar.AddTool(Menu.ID_SAVE, "", load_and_resize_image('save.png'), wx.NullBitmap, shortHelp=_('Save File') ,longHelp=_('Save the current diagram'), clientData=self.canvas),
										toolbar.AddTool(Menu.ID_SAVEAS, "", load_and_resize_image('save_as.png'), wx.NullBitmap, shortHelp=_('Save File As'), longHelp=_('Save the diagram with an another name'), clientData=self.canvas),
										toolbar.AddTool(wx.ID_UNDO, "", load_and_resize_image('undo.png'), wx.NullBitmap, shortHelp=_('Undo'), longHelp=_('Click to go back, hold to see history'),clientData=self.canvas),
										toolbar.AddTool(wx.ID_REDO, "", load_and_resize_image('redo.png'), wx.NullBitmap, shortHelp=_('Redo'), longHelp=_('Click to go forward, hold to see history'),clientData=self.canvas),
										toolbar.AddTool(Menu.ID_ZOOMIN_DIAGRAM, "", load_and_resize_image('zoom+.png'), wx.NullBitmap, shortHelp=_('Zoom +'), longHelp=_('Zoom in'),clientData=self.canvas),
										toolbar.AddTool(Menu.ID_ZOOMOUT_DIAGRAM, "", load_and_resize_image('zoom-.png'), wx.NullBitmap, shortHelp=_('Zoom -'), longHelp=_('Zoom out'),clientData=self.canvas),
										toolbar.AddTool(Menu.ID_UNZOOM_DIAGRAM, "", load_and_resize_image('no_zoom.png'), wx.NullBitmap, shortHelp=_('AnnuleZoom'), longHelp=_('Initial view'),clientData=self.canvas),
										toolbar.AddTool(Menu.ID_PRIORITY_DIAGRAM, "", load_and_resize_image('priority.png'), shortHelp=_('Priority')),
										toolbar.AddTool(Menu.ID_CHECK_DIAGRAM, "", load_and_resize_image('check_master.png'), shortHelp=_('Check')),
										toolbar.AddTool(Menu.ID_SIM_DIAGRAM, "", load_and_resize_image('simulation.png'), shortHelp=_('Simulation')),
										toolbar.AddTool(self.toggle_list[0], "", load_and_resize_image('direct_connector.png'), shortHelp=_('Direct'), kind=wx.ITEM_CHECK),
										toolbar.AddTool(self.toggle_list[1], "", load_and_resize_image('square_connector.png'), shortHelp=_('Square'), kind=wx.ITEM_CHECK),
										toolbar.AddTool(self.toggle_list[2], "", load_and_resize_image('linear_connector.png'), shortHelp=_('Linear'), kind=wx.ITEM_CHECK)
			]							
		toolbar.EnableTool(wx.ID_UNDO, not self.canvas.stockUndo == [])
		toolbar.EnableTool(wx.ID_REDO, not self.canvas.stockRedo == [])
		toolbar.InsertSeparator(2)
		toolbar.InsertSeparator(5)
		toolbar.InsertSeparator(9)
		toolbar.InsertSeparator(13)
		toolbar.InsertSeparator(17)

		toolbar.ToggleTool(self.toggle_list[0],1)

		#=======================================================================
		### spin control for abstraction hierarchy
		if isinstance(diagram, Container.Diagram):
			level_label = wx.StaticText(toolbar, -1, _("Level "))
			self.spin = wx.SpinCtrl(toolbar, self.toggle_list[3], str(level), (55, 90), (50, -1), min=0, max=10)

			toolbar.AddControl(level_label)
			toolbar.AddControl(self.spin)

			ID_UPWARD = self.toggle_list[4]
			ID_DOWNWARD = self.toggle_list[5]

			self.tools.append(toolbar.AddTool(ID_DOWNWARD, "", load_and_resize_image('downward.png'), shortHelp=_('Downward rules')))
			self.tools.append(toolbar.AddTool(ID_UPWARD, "", load_and_resize_image('upward.png'), shortHelp=_('Upward rules')))
    				
			### update downward and upward button
			toolbar.EnableTool(ID_DOWNWARD, level != 0)
			toolbar.EnableTool(ID_UPWARD, level != 0)
		#=======================================================================

		toolbar.Realize()
		self.SetToolBar(toolbar)
		
		### if Detached frame from block (container or Code)
		### save, save-as and simulation are disabled
		if not isinstance(self.parent, Container.ShapeCanvas):
			#toolbar.EnableTool(Menu.ID_SAVE, False)
			#toolbar.EnableTool(Menu.ID_SAVEAS, False)
			toolbar.EnableTool(Menu.ID_SIM_DIAGRAM, False)
			toolbar.EnableTool(Menu.ID_PRIORITY_DIAGRAM, not 'PyPDEVS' in DEFAULT_DEVS_DIRNAME)
		else:
			toolbar.EnableTool(Menu.ID_SAVEAS, False)

		### Call Printable constructor
		PrintOut.Printable.__init__(self, self.canvas)

		### vertical box
		vbox = wx.BoxSizer(wx.VERTICAL)
		#vbox.Add(toolbar, 0, wx.EXPAND, border = 5)
		vbox.Add(self.canvas, 1, wx.EXPAND, border = 5)

		self.SetSizer(vbox)

		self.CenterOnParent()

		self.statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP)
		self.statusbar.SetFieldsCount(3)
		self.statusbar.SetStatusWidths([-2, -5, -1])

		self.__binding()

	def __binding(self):
		""" Binding event.
				ClOSE event, IDLE event and MOVE event are binding here.
				All other event are binding in the main application thanks to general identifiers
				NB: ID are defined on the Menu.py file
		"""
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		### Transparent management when the frame is moving
		self.Bind(wx.EVT_IDLE, self.OnIdle)
		self.Bind(wx.EVT_MOVE, self.OnMove)
		self.Bind(wx.EVT_TOOL, self.OnSaveFile, id=Menu.ID_SAVE)
		self.Bind(wx.EVT_TOOL, self.OnSaveAsFile, id=Menu.ID_SAVEAS)
		self.Bind(wx.EVT_CLOSE, self.OnClose)

	def OnStayOnTop(self, event):
		"""
		"""

		if self.GetWindowStyle()==self.default_style:
			self.SetWindowStyle(wx.CLIP_CHILDREN | wx.STAY_ON_TOP)
		else:
			self.SetWindowStyle(self.default_style)

	def OnSaveFile(self, event):
		""" Save button has been clicked
		"""
		### OnSaveFile of the mainW is activated
		mainW = getTopLevelWindow()
		mainW.OnSaveFile(event)

	def OnSaveAsFile(self, event):
		""" Save button has been clicked
		"""

		### OnSaveAsFile of the mainW is activated
		self.diagram.modify = False
		Container.Block.OnExport(self.diagram, event)

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
		### bug fixe for windows since wx 4.0
		if sys.platform.startswith('win'):
			try:
				canvas.OnLeftDown(event)
				canvas.OnLeftUp(event)
			except:
				pass

		canvas.Refresh()
		### Destroy the windows
		self.Destroy()

		event.Skip()