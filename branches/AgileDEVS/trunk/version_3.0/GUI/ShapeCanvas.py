# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# ShapeCanvas.py ---
#                     --------------------------------
#                          Copyright (c) 2013
#                           Laurent CAPOCCHI
#                        Andre-Toussaint Luciani
#                         University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 04/03/2013
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

import os
import sys
import cPickle
import inspect
import zipfile
import copy

import wx
import wx.wizard as wizmod
import wx.lib.dragscroller
import wx.lib.filebrowsebutton as filebrowse

if __name__ == '__main__':
	import __builtin__
	sys.path.append(os.path.dirname(os.getcwd()))
	__builtin__.__dict__['GUI_FLAG'] = True

import Core.Utilities.Utilities as Utilities
import Core.DomainInterface.DomainBehavior as DomainBehavior
import Core.DomainInterface.DomainStructure as DomainStructure
import Core.Components.Decorators as Decorators
import Core.Patterns.Observer as Observer

import GUI.DropTarget as DropTarget
import GUI.Menu as Menu
import GUI.ConnectDialog as ConnectDialog

import Mixins.Printable as Printable
import Mixins.Selectable as Selectable
import Mixins.Connectable as Connectable
import Mixins.Resizeable as Resizeable

_ = wx.GetTranslation

#Global Stuff -------------------------------------------------
padding = 5
MAX_NB_PORT = 100
MIN_NB_PORT = 0
PORT_RESOLUTION = True


def atomicCode(label):
	return """# -*- coding: utf-8 -*-

\"\"\"
-------------------------------------------------------------------------------
Name:          <filename.py>
Model:         <describe model>
Authors:       <your name>
Organization:  <your organization>
Date:          <yyyy-mm-dd>
License:       <your license>
-------------------------------------------------------------------------------
\"\"\"

### Specific import ------------------------------------------------------------
import Core.DomainInterface.DomainBehavior as DomainBehavior
import Core.DomainInterface.Object as Object

### Model class ----------------------------------------------------------------
class %s(DomainBehavior.DomainBehavior):
	''' DEVS Class for %s model
	'''

	def __init__(self):
		''' Constructor.
		'''
		DomainBehavior.DomainBehavior.__init__(self)

		self.state = {	'status': 'IDLE', 'sigma':INFINITY}

	def extTransition(self):
		''' DEVS external transition function.
		'''
		pass

	def outputFnc(self):
		''' DEVS output function.
		'''
		pass

	def intTransition(self):
		''' DEVS internal transition function.
		'''
		pass

	def timeAdvance(self):
		''' DEVS Time Advance function.
		'''
		return self.state['sigma']

	def finish(self, msg):
		''' Additional function which is lunched just before the end of the simulation.
		'''
		pass
""" % (label, label)


def coupledCode(label):
	return """	


import Core.DomainInterface.DomainStructure as DomainStructure
#======================================================================#
class %s(DomainStructure.DomainStructure):

	def __init__(self):
		DomainStructure.DomainStructure.__init__(self)
""" % label

#-------------------------------------------------------------


class ShapeCanvas(wx.ScrolledWindow, Observer.Subject):
	""" ShapeCanvas class.
	"""

	ID = 0
	CONNECTOR_TYPE = 'direct'

	def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(-1, -1),
				 style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN, name="", diagram=None):
		""" Construcotr
		"""
		import Core.Components.Container as Container
		import GUI.DetachedFrame as DetachedFrame

		wx.ScrolledWindow.__init__(self, parent, id, pos, size, style, name)
		Observer.Subject.__init__(self)

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

		self.stockUndo = Container.FixedList(NB_HISTORY_UNDO)
		self.stockRedo = Container.FixedList(NB_HISTORY_UNDO)

		### subject init
		self.canvas = self
		
		### attach canvas to notebook 1 (for update)
		try:
			self.__state = {}
			mainW = self.GetTopLevelParent()
			mainW = isinstance(mainW, DetachedFrame.DetachedFrame) and wx.GetApp().GetTopWindow() or mainW
			
			self.attach(mainW.nb1)
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

	@Decorators.Post_Undo
	def AddShape(self, shape, after=None):
		self.diagram.AddShape(shape, after)
		self.UpdateShapes([shape])

	def InsertShape(self, shape, index=0):
		self.diagram.InsertShape(shape, index)

	@Decorators.Post_Undo
	def DeleteShape(self, shape):
		self.diagram.DeleteShape(shape)

	def RemoveShape(self, shape):
		self.diagram.DeleteShape(shape)

	@Decorators.Post_Undo
	def keyPress(self, event):
		"""
		"""
		import Core.Components.Container as Container

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
				Utilities.sendEvent(tb, button, wx.CommandEvent(wx.EVT_TOOL.typeId))

			event.Skip()
		elif key == 90 and controlDown and shiftDown:# Redo

			mainW = self.GetTopLevelParent()
			tb = mainW.FindWindowByName('tb')

			### find the tool from toolBar thanks to id
			for tool in mainW.tools:
				if tool.GetId() == wx.ID_REDO:
					button = tool
					break

			if tb.GetToolEnabled(wx.ID_REDO):
				### send commandEvent to simulate undo action on the toolBar
				Utilities.sendEvent(tb, button, wx.CommandEvent(wx.EVT_TOOL.typeId))
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
			for s in filter(lambda shape: not isinstance(shape, Container.ConnectionShape), self.selectedShapes):
				s.OnRotateR(event)
			event.Skip()
		elif key == 76 and controlDown:  # Rotate model on the left
			for s in filter(lambda shape: not isinstance(shape, Container.ConnectionShape), self.selectedShapes):
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
					self.select(self.diagram.shapes[ind + 1])
				except:
					self.select(self.diagram.shapes[0])
			else:
				self.select(self.diagram.shapes[0])
			event.Skip()
		else:
			event.Skip()

		self.Refresh()

	def getWidth(self):
		return self.GetSize()[0]

	def getHeight(self):
		return self.GetSize()[1]

	def DoDrawing(self, dc):
		"""
		"""

		dc.SetUserScale(self.scalex, self.scaley)

		for item in self.diagram.shapes + self.nodes:
			try:
				item.draw(dc)
			except Exception, info:
				sys.stderr.write(_("Draw error: %s \n") % info)

	def OnEraseBackground(self, evt):
		""" Handles the wx.EVT_ERASE_BACKGROUND event"""

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

	@Decorators.Post_Undo
	def OnLock(self, event):
		for s in self.getSelectedShapes():
			if hasattr(s, 'lock'):
				s.lock()

	@Decorators.Post_Undo
	def OnUnLock(self, event):
		for s in self.getSelectedShapes():
			if hasattr(s, 'unlock'):
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
		import Core.Components.Container as Container
		
		# list of node list for
		sourceINodeList = filter(lambda n: not isinstance(n, Container.ResizeableNode) and isinstance(n, Container.INode), self.nodes)
		sourceONodeList = filter(lambda n: not isinstance(n, Container.ResizeableNode) and isinstance(n, Container.ONode), self.nodes)

		# deselect and select target in order to get its list of node (because the node are generated dynamicly)
		self.deselect()
		self.select(target)

		nodesList=filter(lambda n: not isinstance(n, Container.ResizeableNode), self.nodes)

		if isinstance(target,Container.Block):
			if isinstance(source, Container.oPort):
				sourceNodeList = sourceINodeList
				targetNodeList = filter(lambda n: not n in sourceONodeList and isinstance(n,Container.ONode),nodesList)
			elif isinstance(source, Container.iPort):
				sourceNodeList = sourceONodeList
				targetNodeList = filter(lambda n: not n in sourceINodeList and isinstance(n, Container.INode),nodesList)
			else:
				sourceNodeList = sourceONodeList
				if not PORT_RESOLUTION:
					sourceNodeList += sourceINodeList
					targetNodeList = filter(lambda n: not n in sourceNodeList,nodesList)
				else:
					targetNodeList = filter(lambda n: not n in sourceNodeList and isinstance(n, Container.INode),nodesList)

		elif isinstance(target,Container.iPort):
			if isinstance(source, Container.oPort):
				sourceNodeList = sourceINodeList
			elif isinstance(source, Container.iPort):
				sourceNodeList = sourceONodeList
			else:
				sourceNodeList = sourceINodeList

			targetNodeList = filter(lambda n: not n in sourceONodeList and isinstance(n, Container.ONode),nodesList)

		elif isinstance(target,Container.oPort):
			if isinstance(source, Container.oPort):
				sourceNodeList = sourceINodeList
			elif isinstance(source, Container.iPort):
				sourceNodeList = sourceONodeList
			else:
				sourceNodeList = sourceONodeList
			targetNodeList = filter(lambda n: not n in sourceINodeList and isinstance(n, Container.INode),nodesList)
		else:
			targetNodeList = []

		return (sourceNodeList, targetNodeList)
			
	def OnConnectTo(self, event):
		"""
		"""
		import Core.Components.Container as Container

		id = event.GetId()
		menu = event.GetEventObject()

		#source model from diagram
		source = self.getSelectedShapes()[0]

		# Model Name
		targetName = menu.GetLabelText(id)
		sourceName = source.label

		# get target model from its name
		for s in filter(lambda m: not isinstance(m, Container.ConnectionShape), self.diagram.shapes):
			if s.label == targetName:
				target = s
				break

		### init source and taget node list
		self.sourceNodeList, self.targetNodeList = self.GetNodeLists(source, target)
		
		# Now we, if the nodes list are not empty, the connection can be proposed form ConnectDialog
		if self.sourceNodeList != [] and self.targetNodeList != []:
			if len(self.sourceNodeList) == 1 and len(self.targetNodeList) == 1:
				self.makeConnectionShape(self.sourceNodeList[0], self.targetNodeList[0])
			else:
				self.dlgConnection = ConnectDialog.ConnectDialog(wx.GetApp().GetTopWindow(), wx.ID_ANY,
																 _("Connection Manager"), sourceName,
																 self.sourceNodeList, targetName, self.targetNodeList)
				self.dlgConnection.Bind(wx.EVT_BUTTON, self.OnDisconnect, self.dlgConnection._button_disconnect)
				self.dlgConnection.Bind(wx.EVT_BUTTON, self.OnConnect, self.dlgConnection._button_connect)
				self.dlgConnection.Bind(wx.EVT_CLOSE, self.OnCloseConnectionDialog)
				self.dlgConnection.Show()

			self.DiagramModified()

	def OnDisconnect(self, event):
		"""     Disconnect selected ports from connectDialog
		"""
		import Core.Components.Container as Container

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
		sp, tp = self.dlgConnection._result

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
			and len(self.sourceNodeList) == len(self.targetNodeList):
			for sn, tn in map(lambda a, b: (a, b), self.sourceNodeList, self.targetNodeList):
				self.makeConnectionShape(sn, tn)
		### else make simple connection between sp and tp port number of source and target
		else:
			sn = self.sourceNodeList[sp]
			tn = self.targetNodeList[tp]
			self.makeConnectionShape(sn, tn)

		self.Refresh()

	@Decorators.Post_Undo
	def makeConnectionShape(self, sourceNode, targetNode):
		""" Make new ConnectionShape from input number(sp) to output number (tp)
		"""
		import Core.Components.Container as Container
		# preparation et ajout dans le diagramme de la connection
		ci = Container.ConnectionShape()
		self.diagram.shapes.insert(0, ci)

		# connection physique
		if isinstance(sourceNode, Container.ONode):
			ci.setInput(sourceNode.item, sourceNode.index)
			ci.x[0], ci.y[0] = sourceNode.item.getPort('output', sourceNode.index)
			ci.x[1], ci.y[1] = targetNode.item.getPort('input', targetNode.index)
			ci.setOutput(targetNode.item, targetNode.index)

		else:
			ci.setInput(targetNode.item, targetNode.index)
			ci.x[1], ci.y[1] = sourceNode.item.getPort('output', sourceNode.index)
			ci.x[0], ci.y[0] = targetNode.item.getPort('input', targetNode.index)
			ci.setOutput(sourceNode.item, sourceNode.index)

		#ci.ChangeForm(ShapeCanvas.CONNECTOR_TYPE)

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
		import Core.Components.Container as Container
		import Core.Components.Components as Components

		del Container.clipboard[:]
		for m in self.select():
			Container.clipboard.append(m)

		# main windows statusbar update
		Components.printOnStatusBar(self.GetTopLevelParent().statusbar, {0: _('Copy'), 1: ''})

	#def OnScroll(self, event):
	##"""
	##"""
	#event.Skip()

	def OnProperties(self, event):
		""" Properties sub menu has been clicked. Event is transmit to the model
		"""
		# pour passer la fenetre principale a OnProperties qui est deconnecte de l'application du faite de popup
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

		# Create wizard and run
		gmwiz = ModelGeneratorWizard(title=_('DEVSimPy Model Generator'), parent=parent,
									 img_filename=os.path.join('Assets', 'bitmaps', DEVSIMPY_PNG))
		gmwiz.run()

		### just for Mac
		if not gmwiz.canceled_flag:
			return gmwiz
		else:
			return None

	def OnNewModel(self, event):
		""" New model menu has been pressed. Wizard is instanciate.
		"""
		import Core.Components.Container as Container
		import Core.Components.Components as Components
		###mouse postions
		xwindow, ywindow = wx.GetMousePosition()
		x, y = self.ScreenToClientXY(xwindow, ywindow)

		gmwiz = ShapeCanvas.StartWizard(self)

		# if wizard is finished witout closing
		if gmwiz is not None:
			m = Components.BlockFactory.CreateBlock(canvas=self,
													x=x,
													y=y,
													label=gmwiz.label,
													id=gmwiz.id,
													inputs=gmwiz.inputs,
													outputs=gmwiz.outputs,
													python_file=gmwiz.python_path,
													model_file=gmwiz.model_path,
													specific_behavior=gmwiz.specific_behavior)
			if m:

				### save visual model
				if gmwiz.overwrite_flag and isinstance(m, Container.Block):
					if m.SaveFile(gmwiz.model_path):
						m.last_name_saved = gmwiz.model_path
					else:
						dlg = wx.MessageDialog(self, _('Error saving file %s\n') % os.path.basename(gmwiz.model_path), _('Error'), wx.OK | wx.ICON_ERROR)
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

	@Decorators.BuzyCursorNotification
	def OnPaste(self, event):
		""" Paste menu has been clicked.
		"""
		import Core.Components.Container as Container
		import Core.Components.Components as Components

		D = {}  # correspondance between the new and the paste model
		L = []  # list of original connectionShape components

		for m in Container.clipboard:
			if isinstance(m, Container.ConnectionShape):
				L.append(copy.copy(m))
			else:
				# make new shape
				newShape = m.Copy()
				# store correspondance (for coupling)
				D[m] = newShape
				# move new modele
				newShape.x[0] += 35
				newShape.x[1] += 35
				newShape.y[0] += 35
				newShape.y[1] += 35
				### adding model
				self.AddShape(newShape)

		### adding connectionShape
		for cs in L:
			cs.input = (D[cs.input[0]], cs.input[1])
			cs.output = (D[cs.output[0]], cs.output[1])
			self.AddShape(cs)

		# specify the operation in status bar
		Components.printOnStatusBar(self.GetTopLevelParent().statusbar, {0: _('Paste'), 1: ''})

	def OnCut(self, event):
		""" Cut menu has been clicked. Copy and delete event.
		"""

		self.OnCopy(event)
		self.OnDelete(event)

	def OnDelete(self, event):
		"""     Delete menu has been clicked. Delete all selected shape.
		"""

		for s in self.select():
			self.diagram.DeleteShape(s)

		self.DiagramModified()
		self.deselect()

	def DiagramReplace(self, d):

		self.diagram = d

		self.DiagramModified()
		self.deselect()
		self.Refresh()

	def OnRightUp(self, event):
		"""
		"""
		try:
			self.getCurrentShape(event).OnRightUp(event)
		except AttributeError:
			pass

	def OnRightDClick(self, event):
		"""
		"""
		try:
			self.getCurrentShape(event).OnRightDClick(event)
		except AttributeError:
			pass

	def OnLeftDClick(self, event):
		"""
		"""

		model = self.getCurrentShape(event)
		if model:
			if model.OnLeftDClick:
				model.OnLeftDClick(event)
			else:
				wx.MessageBox(_("An error is occured during plugins importation.\nCheck plugins module."))

	def Undo(self):

		mainW = self.GetTopLevelParent()

		### dump solution
		### if parent is not none, the dumps dont work because parent is copy of a class
		try:
			t = cPickle.loads(self.stockUndo[-1])
			### we add new undo of diagram has been modified or one of the shape in diagram sotried in stockUndo has been modified.
			if t.__dict__ != self.diagram.__dict__ \
				or any(objA.__dict__ != objB.__dict__ for objA in self.diagram.GetShapeList() for objB in
					   t.GetShapeList()):
				self.stockUndo.append(cPickle.dumps(obj=self.diagram, protocol=0))
		except IndexError:
			### this is the first call of Undo and StockUnso is emplty
			self.stockUndo.append(cPickle.dumps(obj=self.diagram, protocol=0))
		except TypeError, error:
			sys.stdout.write(_("Error trying to undo: %s \n" % error))
		finally:

			### just for init (white diagram)
			if self.diagram.GetBlockCount() >= 1:
				### toolBar
				tb = mainW.FindWindowByName('tb')
				tb.EnableTool(wx.ID_UNDO, True)

				self.diagram.parent = self
				### note that the diagram is modified
				self.diagram.modify = True
				self.DiagramModified()

	def OnLeftDown(self, event):
		"""
		"""
		import Core.Components.Container as Container

		if self.timer.IsRunning():
			self.timer.Stop()

		item = self.getCurrentShape(event)

		if item is None:   #clicked on empty space deselect all
			self.deselect()

			## Left mouse button down, change cursor to
			## something else to denote event capture
			self.CaptureMouse()
			self.overlay = wx.Overlay()
			self.selectionStart = event.Position

		else:

			# si element pas encore selectionne alors selectionne et pas les autres
			if item not in self.getSelectedShapes():

				item.OnLeftDown(event) # send leftdown event to current shape
				if isinstance(item, Selectable.Selectable) and not event.ShiftDown():
					self.deselect()

				self.select(item)

			# sinon les autres aussi participes
			else:

				for s in self.getSelectedShapes():
					s.OnLeftDown(event) # send leftdown event to current shape

		if not isinstance(item, Container.ConnectionShape) and not isinstance(item, Container.Node):
			### Update the nb1 panel properties
			self.__state['model'] = item
			self.__state['canvas'] = self
			self.notify()

		# main windows statusbar update
		#Components.printOnStatusBar(self.GetTopLevelParent().statusbar, {0:'', 1:''})

		self.Refresh()

	#wx.CallAfter(self.SetFocus)

	###
	@Decorators.Post_Undo
	def OnLeftUp(self, event):
		"""
		"""
		import Core.Components.Container as Container

		shape = self.getCurrentShape(event)

		self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

		### clic sur un block
		if shape is not None:

			shape.OnLeftUp(event)
			shape.leftUp(self.select())

			remove = True
			### empty connection manager
			for item in filter(lambda s: isinstance(s, Container.ConnectionShape), self.select()):
				### restore solid connection
				if len(item.pen) > 2:
					item.pen[2] = wx.SOLID

				if None in (item.output, item.input):

					### gestion des ajouts de connections automatiques
					for ss in filter(lambda a: isinstance(a, Container.Block), self.diagram.GetShapeList()):
						try:
							### si le shape cible (ss) n'est pas le shape que l'on est en train de traiter (pour eviter les auto-connexions)
							if (shape.item.output is not None and ss not in shape.item.output) or \
									(shape.item.input is not None and ss not in shape.item.input):
								x = ss.x[0] * self.scalex
								y = ss.y[0] * self.scaley
								w = (ss.x[1] - ss.x[0]) * self.scalex
								h = (ss.y[1] - ss.y[0]) * self.scaley
								recS = wx.Rect(x, y, w, h)

								### extremite de la connectionShape
								extrem = event.GetPosition()

								### si l'extremite est dans le shape cible (ss)
								if (ss.x[0] <= extrem[0] <= ss.x[1]) and (ss.y[0] <= extrem[1] <= ss.y[1]):

									### new link request
									dlg = wx.TextEntryDialog(self, _('Choose the port number.\nIf doesn\'t exist, we create it.'), _('Coupling Manager'))
									if item.input is None:
										dlg.SetValue(str(ss.output))
										if dlg.ShowModal() == wx.ID_OK:
											try:
												val = int(dlg.GetValue())
											### is not digit
											except ValueError:
												pass
											else:
												if val >= ss.output:
													nn = ss.output
													ss.output += 1
												else:
													nn = val
												item.input = (ss, nn)
												### dont avoid the link
												remove = False
									else:
										dlg.SetValue(str(ss.input))
										if dlg.ShowModal() == wx.ID_OK:
											try:
												val = int(dlg.GetValue())
											### is not digit
											except ValueError:
												pass
											else:
												if val >= ss.input:
													nn = ss.input
													ss.input += 1
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

		### clique sur le canvas
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
					x = s.x[0] * self.scalex
					y = s.y[0] * self.scaley
					w = (s.x[1] - s.x[0]) * self.scalex
					h = (s.y[1] - s.y[0]) * self.scaley
					recS = wx.Rect(x, y, w, h)

					# si les deux rectangles se chevauche
					try:
						if self.permRect.ContainsRect(recS):
							self.select(s)
					except AttributeError:
						raise (_("use >= wx-2.8-gtk-unicode library"))
					#clear out any existing drawing

		self.Refresh()

	def OnTimer(self, event):
		if self.f:
			self.f.Show()

	def OnMouseEnter(self, event):
		self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

	def OnMouseLeave(self, event):
		pass

	#self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

	def DiagramModified(self):
		""" Modification printing in statusbar and modify value manager.

				This method manage the propagation of modification
				from window where modifications are performed to DEVSimpy main window

		"""
		import Core.Components.Components as Components
		import GUI.DetachedFrame as DetachedFrame

		if self.diagram.modify:
			### window where modification is performed
			win = self.GetTopLevelParent()

			if isinstance(win, DetachedFrame.DetachedFrame):
				### main window
				mainW = wx.GetApp().GetTopWindow()
				
				if not isinstance(mainW, DetachedFrame.DetachedFrame):
					nb = mainW.nb2
					canvas = nb.GetPage(nb.GetSelection())
					diagram = canvas.GetDiagram()
					### modifying propagation
					diagram.modify = True
					### update general shapes
					canvas.UpdateShapes()

					label = nb.GetPageText(nb.GetSelection())

					### modified windows dictionary
					D = {win.GetTitle(): win, label: mainW}
				else:
					D={}
			else:
				nb = win.nb2
				canvas = nb.GetPage(nb.GetSelection())
				diagram = canvas.GetDiagram()
				diagram.modify = True
				label = win.nb2.GetPageText(win.nb2.GetSelection())

				D = {label: win}

			#nb.SetPageText(nb.GetSelection(), "*%s"%label.replace('*',''))

			### statusbar printing
			for string, win in D.items():
				Components.printOnStatusBar(win.statusbar, {0: "%s %s" % (string, _("modified")),
															1: os.path.basename(diagram.last_name_saved), 2: ''})

			win.FindWindowByName('tb').EnableTool(Menu.ID_SAVE, self.diagram.modify)

	###
	def OnMotion(self, event):
		""" Motion manager.
		"""
		import Core.Components.Container as Container

		if event.Dragging() and event.LeftIsDown():

			self.diagram.modify = False

			point = self.getEventCoordinates(event)
			x = point[0] - self.currentPoint[0]
			y = point[1] - self.currentPoint[1]

			for s in self.getSelectedShapes():
				s.move(x, y)

				### change cursor when resizing model
				if isinstance(s, Container.ResizeableNode):
					self.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))

				### change cursor when connectionShape hit a node
				elif isinstance(s, Container.ConnectionShape):
					### dot trace to prepare connection
					if len(s.pen) > 2:
						s.pen[2] = wx.DOT

					self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))

					for node in filter(lambda n: isinstance(n, Container.ConnectableNode), self.nodes):
						if node.HitTest(point[0], point[1]):
							self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
						#else:
							#self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
							
					## list of shape connected to the connectionShape (for exclude these of the catching engine)
					#L = s.input or ()
					#L += s.output or ()

					#### try to catch connectionShape with block
					#for ss in filter(lambda n: (isinstance(n, Container.Block) or isinstance(n, Port) ) and n not in L, self.diagram.shapes):
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
										#touch = True
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

			if not self.getSelectedShapes():
				# User is dragging the mouse, check if
				# left button is down
				if self.HasCapture():
					self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
					dc = wx.ClientDC(self)
					odc = wx.DCOverlay(self.overlay, dc)
					odc.Clear()
					ctx = wx.GraphicsContext_Create(dc)
					ctx.SetPen(wx.GREY_PEN)
					ctx.SetBrush(wx.Brush(wx.Colour(229, 229, 229, 80)))
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
			xm, ym = self.ScreenToClientXY(xwindow, ywindow)

			mainW = self.GetTopLevelParent()

			flag = True
			### find if window exists on the top of model, then inactive the QuickAttributeEditor
			for win in filter(lambda w: w.IsTopLevel(), mainW.GetChildren()):
				if win.IsActive():
					flag = False

			if self.f is not None:
				self.f.Close()
				self.f = None

			for s in filter(lambda m: isinstance(m, Container.Block), self.diagram.GetShapeList()):
				x = s.x[0] * self.scalex
				y = s.y[0] * self.scaley
				w = (s.x[1] - s.x[0]) * self.scalex
				h = (s.y[1] - s.y[0]) * self.scaley

				# if mousse over hight the shape
				try:

					if (x <= xm < x + w) and (y <= ym < y + h):
						if self.isSelected(s) and flag:
							self.f = Container.QuickAttributeEditor(self, wx.ID_ANY, s)
							self.timer.Start(1200)
							break
						else:
							if self.timer.IsRunning():
								self.timer.Stop()

				except AttributeError:
					raise (_("use >= wx-2.8-gtk-unicode library"))

		self.DiagramModified()

	def SetDiagram(self, diagram):
		"""
		"""
		self.diagram = diagram

	def GetDiagram(self):
		""" Return Diagram instance
		"""
		return self.diagram

	def getCurrentShape(self, event):
		"""
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
		""" Give x and y of model m into canvas
		"""
		dx = (m.x[1] - m.x[0])
		dy = (m.y[1] - m.y[0])
		ux, uy = self.getScalledCoordinates(x, y)
		#ux, uy = canvas.CalcUnscrolledPosition(x-dx, y-dy)

		return ux - dx, uy - dy

	def getScalledCoordinates(self, x, y):
		originX, originY = self.GetViewStart()
		unitX, unitY = self.GetScrollPixelsPerUnit()
		return (x + (originX * unitX)) / self.scalex, (y + (originY * unitY)) / self.scaley

	def getEventCoordinates(self, event):
		"""
		"""
		return self.getScalledCoordinates(event.GetX(), event.GetY())

	def getSelectedShapes(self):
		"""
		"""
		return self.selectedShapes

	def isSelected(self, s):
		"""
		"""
		return (s is not None) and (s in self.selectedShapes)

	def getName(self):
		"""
		"""
		return self.name

	def deselect(self, item=None):
		"""
		"""

		if item is None:
			for s in self.selectedShapes:
				s.OnDeselect(None)
			del self.selectedShapes[:]
			del self.nodes[:]
		else:
			self.nodes = [n for n in self.nodes if n.item != item]
			self.selectedShapes = [n for n in self.selectedShapes if n != item]
			item.OnDeselect(None)

	### selectionne un shape
	def select(self, item=None):
		""" Select the models in param item
		"""
		import Core.Components.Container as Container

		if item is None:
			return self.selectedShapes

		if isinstance(item, Container.Node):
			del self.selectedShapes[:]
			self.selectedShapes.append(item) # items here is a single node
			return

		if not self.isSelected(item):
			self.selectedShapes.append(item)
			item.OnSelect(None)
			if isinstance(item, Connectable.Connectable):
				self.nodes.extend([Container.INode(item, n, self) for n in xrange(item.input)])
				self.nodes.extend([Container.ONode(item, n, self) for n in xrange(item.output)])
			if isinstance(item, Resizeable.Resizeable):
				self.nodes.extend([Container.ResizeableNode(item, n, self) for n in xrange(len(item.x))])

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

	### selection sur le canvas les Container.ONodes car c'est le seul moyen d'y acceder pour effectuer l'appartenance avec les modeles
	def showOutputs(self, item=None):
		"""
		"""
		import Core.Components.Container as Container

		if item:
			self.nodes.extend([Container.ONode(item, n, self) for n in xrange(item.output)])
		elif item is None:
			for i in self.diagram.shapes:
				if isinstance(i, Connectable.Connectable):
					self.nodes.extend([Container.ONode(i, n, self) for n in xrange(i.output)])

	### selection sur le canvas les Container.INodes car c'est le seul moyen d'y acceder pour effectuer l'appartenance avec les modeles
	def showInputs(self, item=None):
		"""
		"""
		import Core.Components.Container as Container

		if isinstance(item, Container.Block):
			self.nodes.extend([Container.INode(item, n, self) for n in xrange(item.input)])
		else:
			for i in self.diagram.shapes:
				if isinstance(i, Connectable.Connectable):
					self.nodes.extend([Container.INode(i, n, self) for n in xrange(i.input)])

	def GetState(self):
		return self.__state



class TextObjectValidator(wx.PyValidator):
	""" TextObjectValidator()
	"""

	def __init__(self):
		wx.PyValidator.__init__(self)

	def Clone(self):
		return TextObjectValidator()

	def Validate(self, win):
		textCtrl = self.GetWindow()
		text = textCtrl.GetValue()

		if len(text.strip().split(' ')) > 1:
			wx.MessageBox(_("The field must contain a string without space!"), _("Info"))
			textCtrl.SetBackgroundColour("pink")
			textCtrl.SetFocus()
			textCtrl.Refresh()
			return False
		else:
			textCtrl.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
			textCtrl.Refresh()
			return True

	def TransferToWindow(self):
		return True # Prevent wxDialog from complaining.

	def TransferFromWindow(self):
		return True # Prevent wxDialog from complaining.


class wizard_page(wizmod.PyWizardPage):
	""" An extended panel obj with a few methods to keep track of its siblings.  
	This should be modified and added to the wizard.  Season to taste."""

	def __init__(self, parent, title):
		wx.wizard.PyWizardPage.__init__(self, parent)
		self.next = self.prev = None
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.title = wx.StaticText(self, wx.ID_ANY, title)
		self.title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.sizer.AddWindow(self.title, 0, wx.ALIGN_LEFT | wx.ALL, padding)
		self.sizer.AddWindow(wx.StaticLine(self, wx.ID_ANY), 0, wx.EXPAND | wx.ALL, padding)
		self.SetSizer(self.sizer)

	def add_stuff(self, stuff):
		"""Add aditional widgets to the bottom of the page"""
		self.sizer.Add(stuff, 0, wx.EXPAND | wx.ALL, padding)

	def SetNext(self, next):
		"""Set the next page"""
		self.next = next

	def SetPrev(self, prev):
		"""Set the previous page"""
		self.prev = prev

	def GetNext(self):
		"""Return the next page"""
		return self.next

	def GetPrev(self):
		"""Return the previous page"""
		return self.prev


class Wizard(wx.wizard.Wizard):
	"""Add pages to this wizard object to make it useful."""

	def __init__(self, title, parent, img_filename=""):
		""" Constructor
		"""
		if img_filename and os.path.exists(img_filename):
			img = wx.Bitmap(img_filename)
		else:
			img = wx.NullBitmap
		wx.wizard.Wizard.__init__(self, parent, wx.ID_ANY, title, img)

		self.SetPageSize((400, 300))

		# pages list
		self.pages = []

		#flag
		self.canceled_flag = False
		self.overwrite_flag = True

		# Lets catch the events
		self.Bind(wizmod.EVT_WIZARD_PAGE_CHANGED, self.on_page_changed)
		self.Bind(wizmod.EVT_WIZARD_PAGE_CHANGING, self.on_page_changing)
		self.Bind(wizmod.EVT_WIZARD_CANCEL, self.on_cancel)
		self.Bind(wizmod.EVT_WIZARD_FINISHED, self.on_finished)
		self.Bind(wx.EVT_CLOSE, self.on_close)

	def add_page(self, page):
		"""Add a wizard page to the list."""
		if self.pages:
			previous_page = self.pages[-1]
			page.SetPrev(previous_page)
			previous_page.SetNext(page)
		self.pages.append(page)

	def run(self):
		self.RunWizard(self.pages[0])

	def on_page_changed(self, evt):
		"""Executed after the page has changed."""
		#if evt.GetDirection():  dir = "forward"
		#else:                   dir = "backward"
		#page = evt.GetPage()
		pass

	def on_page_changing(self, evt):
		"""Executed before the page changes, so we might veto it."""
		#if evt.GetDirection():  dir = "forward"
		#else:                   dir = "backward"
		#page = evt.GetPage()
		pass

	def on_cancel(self, evt):
		"""Cancel button has been pressed.  Clean up and exit without continuing."""
		self.canceled_flag = True
		self.on_close(evt)

	def on_finished(self, evt):
		"""Finish button has been pressed.  Give the specified values
		"""
		pass

	def on_close(self, evt):
		""" Close button has been pressed. Destroy the wizard.
		"""
		self.canceled_flag = True
		self.Destroy()


class ModelGeneratorWizard(Wizard):
	""" Model Generator Wizard Class.
	"""

	def __init__(self, *args, **kwargs):
		""" Constructor
		"""
		import Core.Components.Components as Components
		import GUI.DetachedFrame as DetachedFrame

		Wizard.__init__(self, *args, **kwargs)

		# properties of model
		self.type = "Atomic"
		self.label = ""
		self.inputs = 1
		self.outputs = 1
		self.python_path = ""
		self.model_path = ""
		self.specific_behavior = ""

		# special properties for Port
		self.id = None

		# canvas parent
		parent = self.GetParent()

		# Create a page 1
		page1 = wizard_page(self, _('Type of Model'))
		bt1 = wx.RadioButton(page1, wx.ID_ANY, _('Atomic model'), style=wx.RB_GROUP)
		bt2 = wx.RadioButton(page1, wx.ID_ANY, _('Coupled model'))
		bt1.SetToolTipString(
			_("DEVS classic atomic model. It is used to define the behavior (or a part of behavior) of the system"))
		bt2.SetToolTipString(
			_("DEVS classic coupled model. It is used to define the structure (or a part of structure) of the system"))
		page1.add_stuff(wx.StaticText(page1, wx.ID_ANY, _('Choose the type of model:')))
		page1.add_stuff(bt1)
		page1.add_stuff(bt2)

		### if left click on the DetachedFrame, port instance can be created
		if isinstance(parent.GetTopLevelParent(), DetachedFrame.DetachedFrame):
			bt3 = wx.RadioButton(page1, wx.ID_ANY, _('Input Port'))
			bt4 = wx.RadioButton(page1, wx.ID_ANY, _('Output Port'))
			bt3.SetToolTipString(_("DEVS classic input model. It is used to link models"))
			bt4.SetToolTipString(_("DEVS classic output model. It is used to link models"))
			page1.add_stuff(bt3)
			page1.add_stuff(bt4)

			def onBt3Click(evt):
				""" input port radio button has been pressed. We redefine its action
				"""

				self.type = "IPort"
				page1.SetNext(page6)
				page6.SetNext(page5)
				page5.SetNext(None)
				page5.SetPrev(page1)
				page6.SetPrev(page1)

			def onBt4Click(evt):
				""" input port radio button has been pressed. We redefine its action
				"""

				self.type = "OPort"
				page1.SetNext(page7)
				page7.SetNext(page5)
				page5.SetNext(None)
				page5.SetPrev(page1)
				page7.SetPrev(page1)

			bt3.Bind(wx.EVT_RADIOBUTTON, onBt3Click)
			bt4.Bind(wx.EVT_RADIOBUTTON, onBt4Click)

		def python_path_call_back(evt):
			fn = evt.GetEventObject().GetValue()
			cls = Components.GetClass(fn)
			if inspect.isclass(cls):
				if not (
					issubclass(cls, DomainBehavior.DomainBehavior) or issubclass(cls, DomainStructure.DomainStructure)):
					dlg = wx.MessageDialog(parent, _(
						'The python file must contain a class that inherit of DomainBehavior or DomainStructure master class.\n Please choose a correct python file.'),
										   _('Error'), wx.OK | wx.ICON_ERROR)
					dlg.ShowModal()
			else:
				dlg = wx.MessageDialog(parent, _(
					'The python file not includes a class definition.\n Please choose a correct python file.'),
									   _('Error'), wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()

		def plugin_path_call_back(evt):
			fn = evt.GetEventObject().GetValue()
			if os.path.basename(fn) != 'plugins.py':
				dlg = wx.MessageDialog(parent, _(
					'The name of plugin python file must be plugins.py.\n Please choose a correct plugin python file.'),
									   _('Error'), wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()

		# Create a page 2
		page2 = wizard_page(self, _('Atomic Model (AMD)'))
		sb1 = wx.StaticBoxSizer(wx.StaticBox(page2, wx.ID_ANY, _('Properties')), orient=wx.VERTICAL)
		vb1 = wx.BoxSizer(wx.VERTICAL)
		vbox2 = wx.GridSizer(6, 2, 3, 3)
		bt5 = wx.CheckBox(page2, wx.ID_ANY, _('Default python file'))
		bt5.SetValue(True)
		bt5.SetToolTipString(_("Choose python file from specific directory"))
		bt51 = wx.CheckBox(page2, wx.ID_ANY, _('No plugin file'))
		bt51.SetToolTipString(_("Choose plugin file from specific directory"))
		bt51.SetValue(True)
		cb0 = wx.ComboBox(page2, wx.ID_ANY, 'Default',
						  choices=[_('Default'), _('Generator'), _('Viewer'), _('Collector')], style=wx.CB_READONLY)
		# filebrowse properties
		fb1 = filebrowse.FileBrowseButton(page2, wx.ID_ANY, startDirectory=DOMAIN_PATH, labelText="", fileMask='*.py',
										  toolTip=bt5.GetToolTip().GetTip(), changeCallback=python_path_call_back)
		fb12 = filebrowse.FileBrowseButton(page2, wx.ID_ANY, startDirectory=DOMAIN_PATH, labelText="",
										   fileMask='plugins.py', toolTip=bt51.GetToolTip().GetTip(),
										   changeCallback=python_path_call_back)
		fb1.Enable(False)
		fb12.Enable(False)
		vbox2.AddMany(
			[(wx.StaticText(page2, wx.ID_ANY, _('Label')), 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
			 (wx.TextCtrl(page2, wx.ID_ANY, value=_("Atomic_Name"), validator=TextObjectValidator()), 0,
			  wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
			 (wx.StaticText(page2, wx.ID_ANY, _('Specific Behavior')), 0,
			  wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
			 (cb0, 0, wx.EXPAND),
			 (wx.StaticText(page2, wx.ID_ANY, _('Inputs')), 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
			 (wx.SpinCtrl(page2, wx.ID_ANY, '1', min=MIN_NB_PORT, max=MAX_NB_PORT), 0, wx.EXPAND),
			 (wx.StaticText(page2, wx.ID_ANY, _('Outputs')), 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
			 (wx.SpinCtrl(page2, wx.ID_ANY, '1', min=MIN_NB_PORT, max=MAX_NB_PORT), 0, wx.EXPAND),
			 (bt5, 0),
			 (fb1, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
			 (bt51, 0),
			 (fb12, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
			])
		vb1.Add(vbox2, 0, wx.EXPAND)
		sb1.Add(vb1, 0, wx.EXPAND)

		page2.add_stuff(sb1)

		# Create a page 3
		page3 = wizard_page(self, _('Coupled Model (CMD)'))
		sb2 = wx.StaticBoxSizer(wx.StaticBox(page3, wx.ID_ANY, _('Properties')), orient=wx.VERTICAL)
		vb2 = wx.BoxSizer(wx.VERTICAL)
		vbox3 = wx.GridSizer(6, 2, 3, 3)
		bt6 = wx.CheckBox(page3, wx.ID_ANY, _('Default python file'))
		bt6.SetToolTipString(bt5.GetToolTip().GetTip())
		bt6.SetValue(True)
		bt61 = wx.CheckBox(page3, wx.ID_ANY, _('No plugin file'))
		bt61.SetToolTipString(bt51.GetToolTip().GetTip())
		bt61.SetValue(True)
		# filebrowse properties
		fb4 = filebrowse.FileBrowseButton(page3, wx.ID_ANY, startDirectory=DOMAIN_PATH, labelText="", fileMask='*.py',
										  toolTip=bt6.GetToolTip().GetTip(), changeCallback=plugin_path_call_back)
		fb41 = filebrowse.FileBrowseButton(page3, wx.ID_ANY, startDirectory=DOMAIN_PATH, labelText="",
										   fileMask='plugins.py', toolTip=bt61.GetToolTip().GetTip(),
										   changeCallback=plugin_path_call_back)
		fb4.Enable(False)
		fb41.Enable(False)
		vbox3.AddMany(
			[(wx.StaticText(page3, wx.ID_ANY, _('Label')), 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
			 (wx.TextCtrl(page3, wx.ID_ANY, value=_("Coupled_Name"), validator=TextObjectValidator()), 0,
			  wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
			 (wx.StaticText(page3, wx.ID_ANY, _('Inputs')), 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
			 (wx.SpinCtrl(page3, wx.ID_ANY, '1', min=MIN_NB_PORT, max=MAX_NB_PORT), 0, wx.EXPAND),
			 (wx.StaticText(page3, wx.ID_ANY, _('Outputs')), 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
			 (wx.SpinCtrl(page3, wx.ID_ANY, '1', min=MIN_NB_PORT, max=MAX_NB_PORT), 0, wx.EXPAND),
			 (bt6, 0),
			 (fb4, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
			 (bt61, 0),
			 (fb41, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
			])
		#page3.add_stuff(vbox3)
		vb2.Add(vbox3, 0, wx.EXPAND)
		sb2.Add(vb2, 0, wx.EXPAND)
		page3.add_stuff(sb2)

		# Create a page 4_1
		page4_1 = wizard_page(self, _('Finish'))
		# save filebrowse
		init = os.path.join(DOMAIN_PATH, "%s.amd" % vbox2.GetItem(1).GetWindow().GetValue())
		fb2 = filebrowse.FileBrowseButton(page4_1,
										  wx.ID_ANY,
										  initialValue=init,
										  fileMode=wx.SAVE,
										  #startDirectory = DOMAIN_PATH,
										  labelText=_("Save as"),
										  fileMask='*.amd')

		page4_1.add_stuff(fb2)

		# Create a page 4_2
		page4_2 = wizard_page(self, _('Finish'))
		init = os.path.join(DOMAIN_PATH, "%s.cmd" % vbox3.GetItem(1).GetWindow().GetValue())
		# save filebrowse
		fb3 = filebrowse.FileBrowseButton(page4_2,
										  wx.ID_ANY,
										  initialValue=init,
										  fileMode=wx.SAVE,
										  #startDirectory = DOMAIN_PATH,
										  labelText=_("Save as"),
										  fileMask='*.cmd')
		page4_2.add_stuff(fb3)

		# Create a page 5
		page5 = wizard_page(self, _('Finish'))
		page5.add_stuff(wx.StaticText(page5, wx.ID_ANY, _('Port model has been created.')))

		### if left click on the DetachedFrame, port instance can be created
		if isinstance(parent.GetTopLevelParent(), DetachedFrame.DetachedFrame):
			# Create a page 6
			page6 = wizard_page(self, _('Input Port'))
			sb3 = wx.StaticBoxSizer(wx.StaticBox(page6, wx.ID_ANY, _('Properties')), orient=wx.VERTICAL)
			vb3 = wx.BoxSizer(wx.VERTICAL)
			#page6.add_stuff(wx.StaticBox(page6, -1, _('Properties')))
			cb_id1 = wx.CheckBox(page6, wx.ID_ANY, _('Automatic Id'))
			spin_id1 = wx.SpinCtrl(page6, wx.ID_ANY, str(parent.diagram.GetiPortCount()), min=MIN_NB_PORT,
								   max=MAX_NB_PORT)
			cb_id1.SetValue(True)
			spin_id1.Enable(False)
			vbox6 = wx.GridSizer(2, 2, 3, 3)
			vbox6.AddMany(
				[(wx.StaticText(page6, wx.ID_ANY, _('Label')), 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
				 (wx.TextCtrl(page6, wx.ID_ANY, value=_("IPort ")), 0,
				  wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
				 (cb_id1, 0),
				 (spin_id1, 0, wx.EXPAND)
				])
			vb3.Add(vbox6, 0, wx.EXPAND)
			sb3.Add(vb3, 0, wx.EXPAND)

			page6.add_stuff(sb3)
			#page6.add_stuff(vbox6)

			# Create a page 7
			page7 = wizard_page(self, _('Output Port'))
			#page7.add_stuff(wx.StaticBox(page7, -1, _('Properties')))
			sb4 = wx.StaticBoxSizer(wx.StaticBox(page7, wx.ID_ANY, _('Properties')), orient=wx.VERTICAL)
			vb4 = wx.BoxSizer(wx.VERTICAL)
			cb_id2 = wx.CheckBox(page7, wx.ID_ANY, _('Automatic Id'))
			spin_id2 = wx.SpinCtrl(page7, wx.ID_ANY, str(parent.diagram.GetoPortCount()), min=MIN_NB_PORT,
								   max=MAX_NB_PORT)
			cb_id2.SetValue(True)
			spin_id2.Enable(False)
			vbox7 = wx.GridSizer(2, 2, 3, 3)
			vbox7.AddMany(
				[(wx.StaticText(page7, wx.ID_ANY, _('Label')), 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
				 (wx.TextCtrl(page7, wx.ID_ANY, value=_("OPort ")), 0,
				  wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL),
				 (cb_id2, 0),
				 (spin_id2, 0, wx.EXPAND)
				])
			vb4.Add(vbox7, 0, wx.EXPAND)
			sb4.Add(vb4, 0, wx.EXPAND)

			page7.add_stuff(sb4)

		def onBt1Click(evt):
			""" Atomic radio button has been pressed. We redefine its action
			"""

			self.type = "Atomic"
			page1.SetNext(page2)
			page2.SetPrev(page1)
			page2.SetNext(page4_1)
			page4_1.SetPrev(page2)

		def onBt2Click(evt):
			""" Coupled radio button has been pressed. We redefine its action
			"""

			self.type = "Coupled"
			page1.SetNext(page3)
			page3.SetPrev(page1)
			page3.SetNext(page4_2)
			page4_2.SetPrev(page3)

		# event handler for check button
		def onBt5Check(evt):
			""" Python file selector is cheked.
			"""

			if evt.GetEventObject().GetValue():
				fb1.Enable(False)
			else:
				fb1.Enable(True)

		# event handler for check button
		def onBt51Check(evt):
			""" Python file selector is cheked.
			"""
			if evt.GetEventObject().GetValue():
				fb12.Enable(False)
			else:
				fb12.Enable(True)

		def onBt6Check(evt):
			""" Python file selector is cheked.
			"""

			if evt.GetEventObject().GetValue():
				fb4.Enable(False)
			else:
				fb4.Enable(True)

		# event handler for check button
		def onBt61Check(evt):
			""" Python file selector is cheked.
			"""
			if evt.GetEventObject().GetValue():
				fb41.Enable(False)
			else:
				fb41.Enable(True)

		def onCbId1(evt):
			if evt.GetEventObject().GetValue():
				spin_id1.Enable(False)
			else:
				spin_id1.Enable(True)

		def onCbId2(evt):
			if evt.GetEventObject().GetValue():
				spin_id2.Enable(False)
			else:
				spin_id2.Enable(True)

		def OnSpecificBehavior(evt):
			""" Give the control on the number of input and output form specific behavior choice
			"""

			### specific behavoir choice
			val = evt.GetEventObject().GetValue()

			### if generator, 0 input and x output (1 is the default)
			if val == _('Generator'):

				### no input and
				vbox2.GetItem(5).GetWindow().SetValue(0)
				### update output
				if vbox2.GetItem(7).GetWindow().GetValue() == 0:
					vbox2.GetItem(7).GetWindow().SetValue(1)

				### Deasable the choice
				vbox2.GetItem(4).GetWindow().Enable(False)
				vbox2.GetItem(5).GetWindow().Enable(False)
				### Enable the output choice
				vbox2.GetItem(6).GetWindow().Enable(True)
				vbox2.GetItem(7).GetWindow().Enable(True)

			### if collector, 0 output and x input (1 is the default)
			elif val in (_('Collector'), _('Viewer')):
				### no output
				vbox2.GetItem(7).GetWindow().SetValue(0)

				### update input
				if vbox2.GetItem(5).GetWindow().GetValue() == 0:
					vbox2.GetItem(5).GetWindow().SetValue(1)

				### Deasable the choice
				vbox2.GetItem(7).GetWindow().Enable(False)
				vbox2.GetItem(6).GetWindow().Enable(False)
				### Enable the output choice
				vbox2.GetItem(5).GetWindow().Enable(True)
				vbox2.GetItem(4).GetWindow().Enable(True)

			### if Default, 1 output and input
			else:
				vbox2.GetItem(5).GetWindow().Enable(True)
				vbox2.GetItem(4).GetWindow().Enable(True)
				vbox2.GetItem(6).GetWindow().Enable(True)
				vbox2.GetItem(7).GetWindow().Enable(True)
				vbox2.GetItem(5).GetWindow().SetValue(1)
				vbox2.GetItem(7).GetWindow().SetValue(1)

		def OnInputAMDLabel(evt):
			fb2.SetValue(os.path.join(DOMAIN_PATH, "%s.amd" % evt.GetString()))

		def OnInputCMDLabel(evt):
			fb3.SetValue(os.path.join(DOMAIN_PATH, "%s.cmd" % evt.GetString()))

		# Binding
		bt1.Bind(wx.EVT_RADIOBUTTON, onBt1Click)
		bt2.Bind(wx.EVT_RADIOBUTTON, onBt2Click)
		bt5.Bind(wx.EVT_CHECKBOX, onBt5Check)
		bt51.Bind(wx.EVT_CHECKBOX, onBt51Check)
		bt6.Bind(wx.EVT_CHECKBOX, onBt6Check)
		bt61.Bind(wx.EVT_CHECKBOX, onBt61Check)
		### if left click on the DetachedFrame, port instance can be created
		if isinstance(parent.GetTopLevelParent(), DetachedFrame.DetachedFrame):
			cb_id1.Bind(wx.EVT_CHECKBOX, onCbId1)
			cb_id2.Bind(wx.EVT_CHECKBOX, onCbId2)
		cb0.Bind(wx.EVT_COMBOBOX, OnSpecificBehavior)
		amd_input_label = vbox2.GetItem(1).GetWindow()
		amd_input_label.Bind(wx.EVT_TEXT, OnInputAMDLabel)
		cmd_input_label = vbox3.GetItem(1).GetWindow()
		cmd_input_label.Bind(wx.EVT_TEXT, OnInputCMDLabel)

		# Add some more pages
		self.add_page(page1)
		self.add_page(page2)
		self.add_page(page3)
		self.add_page(page4_1)
		self.add_page(page4_2)
		self.add_page(page5)

		### if left click on the DetachedFrame, port instance can be created
		if isinstance(parent.GetTopLevelParent(), DetachedFrame.DetachedFrame):
			self.add_page(page6)
			self.add_page(page7)

		# define next and prev
		page1.SetNext(page2)
		page2.SetNext(page4_1)
		page2.SetPrev(page1)
		page3.SetPrev(page1)
		page3.SetNext(page4_2)
		page4_1.SetPrev(page2)
		page4_2.SetPrev(page3)
		page4_1.SetNext(None)
		page4_2.SetNext(None)

	def on_finished(self, evt):
		"""Finish button has been pressed. Give the specified values
		"""

		# gridsizer depending on the type of choosing model
		if self.type in ('IPort', 'OPort'):
			page = self.pages[6] if self.type == 'IPort' else self.pages[7]
			gridSizer = page.sizer.GetItem(2).GetSizer().GetItem(0).GetSizer().GetItem(0).GetSizer()
			textCtrl = gridSizer.GetItem(1).GetWindow()
			self.label = textCtrl.GetValue()
			self.id = gridSizer.GetItem(3).GetWindow().GetValue()
			self.python_path = os.path.join(DOMAIN_PATH, 'Basic', self.type + '.py')

		else:

			if self.type == 'Atomic':
				gridSizer = self.pages[1].sizer.GetItem(2).GetSizer().GetItem(0).GetSizer().GetItem(0).GetSizer()
				filebrowse_python = gridSizer.GetItem(9).GetWindow()
				filebrowse_plugin = gridSizer.GetItem(11).GetWindow()
				filebrowse_model = self.pages[3].sizer.GetItem(2).GetWindow()

				### test if extention exists
				model_path = filebrowse_model.GetValue()
				if not model_path.endswith('.amd'):
					model_path += '.amd'

				# give the label
				textCtrl = gridSizer.GetItem(1).GetWindow()
				### give the python filename, inputs and outputs of corresponding model
				in_SpinCtrl = gridSizer.GetItem(5).GetWindow()
				out_SpinCtrl = gridSizer.GetItem(7).GetWindow()
				### give the specific behavior which can be Default, Generator or Collector (Scope and Disk)
				specific_behavior = gridSizer.GetItem(3).GetWindow()
				self.specific_behavior = specific_behavior.GetValue()

			elif self.type == 'Coupled':
				gridSizer = self.pages[2].sizer.GetItem(2).GetSizer().GetItem(0).GetSizer().GetItem(0).GetSizer()
				filebrowse_python = gridSizer.GetItem(7).GetWindow()
				filebrowse_plugin = gridSizer.GetItem(9).GetWindow()
				filebrowse_model = self.pages[4].sizer.GetItem(2).GetWindow()

				### test if extention exists
				model_path = filebrowse_model.GetValue()
				if not model_path.endswith('.cmd'):
					model_path += '.cmd'

				# give the label
				textCtrl = gridSizer.GetItem(1).GetWindow()
				### give the python filename, inputs and outputs of corresponding model
				in_SpinCtrl = gridSizer.GetItem(3).GetWindow()
				out_SpinCtrl = gridSizer.GetItem(5).GetWindow()

			self.model_path = os.path.abspath(model_path)
			self.python_path = filebrowse_python.GetValue()
			self.plugin_path = filebrowse_plugin.GetValue()

			self.label = textCtrl.GetValue()
			self.id = 0
			self.inputs = in_SpinCtrl.GetValue()
			self.outputs = out_SpinCtrl.GetValue()

			### model path exist ?
			if os.path.exists(self.model_path):
				msg = _("%s already exist.\nDo you want to rewrite it ?") % self.model_path
				dlg = wx.MessageDialog(self, msg, _("Question"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
				if dlg.ShowModal() in (wx.ID_NO, wx.ID_CANCEL):
					self.overwrite_flag = False

			if self.overwrite_flag:
				### create the model on the disk
				try:
					zout = zipfile.ZipFile(self.model_path, "w")
				except Exception, info:
					sys.stdout.write(_("ERROR: Enable to creacte Zip file in Wizard GUI (%s)" % info))
					return False
				else:
					if self.python_path == '':
						if self.type == 'Atomic':
							string = atomicCode(self.label)
						else:
							string = coupledCode(self.label)

						python_name = os.path.basename(self.model_path).split('.')[0]

						zout.writestr("%s.py" % python_name, string.encode('utf-8'))

						self.python_path = os.path.join(self.model_path, "%s.py" % python_name)
					else:
						py_file = os.path.basename(self.python_path)
						zout.write(self.python_path, py_file)

						self.python_path = os.path.join(self.model_path, py_file)

					### force model file (.amd or cmd) to have same name with choosed python file
					#ext = os.path.basename(self.model_path).split('.')[1]
					#self.model_path = os.path.join(os.path.dirname(self.model_path), "%s.%s"%(py_file.split('.')[0],ext))

					zout.writestr('DEVSimPyModel.dat', _("Call SaveFile method !"))

					if self.plugin_path != '':
						zout.write(self.plugin_path, os.path.join('plugins',os.path.basename(self.plugin_path)))
				finally:
					zout.close()
			else:
				### search python file in archive
				zin = zipfile.ZipFile(self.model_path, 'r')
				info_list = zin.infolist()
				### si le nom du fichier python py est le meme que le nom du modele .amd ou .cmd
				name = "%s.py" % os.path.splitext(os.path.basename(self.model_path))[0]
				if name in info_list:
					self.python_path = os.path.join(self.model_path, name)
				### sinon on cherche le .py dans le modele en excluant plugins.py
				else:
					for item in info_list:
						name, ext = os.path.splitext(item.filename)
						if ext == ".py" and name != 'plugins':
							self.python_path = os.path.join(self.model_path, item.filename)
							### TODO: get class from python file and test with insepct module if is submodule of DomainBehavior
							break

		return True


#if __name__ == '__main__':

	#app = wx.PySimpleApp()  # Start the application
	
	## Create wizard and add any kind pages you'd like
	#mywiz = ModelGeneratorWizard(_('DEVSimPy Model Generator'), img_filename = os.path.join(os.getcwd(),'bitmaps/IconeDEVSimPy.png'))
	## Show the main window
	#mywiz.run() 
	## Cleanup
	#mywiz.Destroy()
	
	#app.MainLoop()