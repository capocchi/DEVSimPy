# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Container.py ---
#                     --------------------------------
#                        Copyright (c) 2014
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 3.0                                        last modified: 29/01/2013
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
import os
import sys
import inspect
import re
import __builtin__
#import string
import zipfile
import array
#import linecache
import copy
from tempfile import gettempdir

import wx
import wx.lib.dragscroller
#import wx.grid as gridlib
#import wx.gizmos as gizmos
#import wx.lib.imagebrowser as ib
import wx.lib.dialogs

if wx.VERSION_STRING < '2.9':
	from wx.lib.pubsub import Publisher
else:
	from wx.lib.pubsub import pub as Publisher

from wx.lib.newevent import NewEvent
from wx.lib import wordwrap

### wx.color has been removed in wx. 2.9
if hasattr(wx, "Color"):
	wx.Colour = wx.Color
else:
	wx.Color = wx.Colour

_ = wx.GetTranslation
AttrUpdateEvent, EVT_ATTR_UPDATE = NewEvent()

if __builtin__.__dict__['GUI_FLAG'] is False:
	for root, dirs, files in os.walk(os.path.join(os.getcwd(),'Domain')):
		# print "root -> ", root, " - dirs -> ", dirs, " - files ->", files
		sys.path.append(os.path.abspath(root))


#Import GUI
#import GUI.LabelGUI as LabelGUI
import GUI.DiagramConstantsDialog as DiagramConstantsDialog
import GUI.SpreadSheet as SpreadSheet
import GUI.PlotGUI as PlotGUI
import GUI.PriorityGUI as PriorityGUI
import GUI.CheckerGUI as CheckerGUI
import GUI.PluginsGUI as PluginsGUI
from GUI.ShapeCanvas import ShapeCanvas
from GUI.DetachedFrame import DetachedFrame
import GUI.Menu as Menu
import GUI.ZipManager as ZipManager

#Import Core
import Core.Patterns.Observer as Observer
import Core.DomainInterface.MasterModel as MasterModel
import Core.Utilities.Utilities as Utilities
#import Core.Utilities.pluginmanager as pluginmanager
import Core.Components.Decorators as Decorators
import Core.Components.Components as Components
import Core.Simulation.SimulationGUI as SimulationGUI  # SimulationDialog

#Import Mixins
import Mixins.Achievable as Achievable
import Mixins.Attributable as Attributable
import Mixins.Connectable as Connectable
import Mixins.Plugable as Plugable
import Mixins.Resizeable as Resizeable
import Mixins.Rotable as Rotable
import Mixins.Savable as Savable
import Mixins.Selectable as Selectable
import Mixins.Structurable as Structurable
import Mixins.Testable as Testable


#Global Stuff -------------------------------------------------
clipboard = []


##############################################################
#                                                            #
# 					GENERAL fUNCTIONS                        #
#                                                            #
##############################################################

#
# def MsgBoxError(event, parent, msg):
# 	""" Pop-up alert for error in the .py file of a model
# 	"""
#
# 	### si erreur dans l'importation
# 	if isinstance(msg, unicode):
# 		dial = wx.MessageDialog(parent, _('Error trying to import module : %s')%msg, _('Error'), wx.OK | wx.ICON_ERROR)
# 		dial.ShowModal()
# 	### si erreur dans le constructeur (__init__) ou pendant la simulation du .py
# 	elif isinstance(msg, tuple):
# 		### recherche des infos lies a l'erreur
# 		typ, val, tb = msg
# 		try:
#
# 			trace = format_exception(typ, val, tb)[-2].split(',')
#
# 			path,line,fct = trace[0:3]
#
# 		except Exception, info:
# 			path = None
# 			line = None
# 			fct = None
#
# 		if path is not None:
# 			python_path = "File: %s\n"%(path.split(' ')[-1])
# 		else:
# 			python_path = ""
#
# 		if line is not None:
# 			line_number = "Line: %s\n"%(line.split(' ')[-1])
# 		else:
# 			line_number = ""
#
# 		if fct is not None:
# 			fct = "Function: %s\n"%(fct.split('\n')[0])
# 		else:
# 			fct = ""
#
# 		if path is not None:
#
# 			### demande si on veut corriger l'erreur
# 			dial = wx.MessageDialog(parent, _("Error: %s\n%s%s%s\nDo you want to remove this error?")%(str(val),str(python_path),str(fct),str(line_number)), _('rror'), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_ERROR)
# 			if dial.ShowModal() == wx.ID_YES:
# 				### il faut supprimer les doubles cote de chaque cotee et caster en string
# 				python_path = str(path.split(' ')[-1])[1:-1]
# 				dir_name = os.path.dirname(python_path)
# 				### creation d'un composant devs temporaire pour l'invocation de l'editeur de code
# 				devscomp = Components.DEVSComponent()
# 				devscomp.setDEVSPythonPath(python_path)
# 				### instanciation de l'editeur de code et pointeur sur la ligne de l'erreur
# 				editor_frame = Components.DEVSComponent.OnEditor(devscomp, event)
# 				if zipfile.is_zipfile(dir_name): editor_frame.cb.model_path = dir_name
# 				if editor_frame:
# 					editor_frame.nb.GetCurrentPage().GotoLine(int(line.split(' ')[-1]))
# 				return True
# 			else:
# 				return False
# 		else:
# 			wx.MessageBox(_("There is errors in python file.\nError trying to translate error informations: %s %s %s")%(typ, val, tb), _("Error"), wx.OK|wx.ICON_ERROR)



	#defGetClass(elem):
	#""" Get python class from filename.
	#"""

	#if elem.startswith('http'):

	#### Get module from url
	#elem =BlockFactory.GetModule(elem)

	#### if no errors
	#if inspect.ismodule(elem):
	#for name, obj in inspect.getmembers(elem):
	#if inspect.isclass(obj) and elem.__name__ in name:
	#return obj
	#### return error
	#else:
	#return elem

	#### if local file path
	#else:

	#clsmembers =getClassMember(elem)

	#if isinstance(clsmembers, dict):
	#moduleName = path_to_module(elem)

	#for cls in clsmembers.values():
	##print 'sdf', str(cls.__module__), moduleName, str(cls.__module__) in str(moduleName)

	#if str(cls.__module__) in str(moduleName):
	#return cls
	#else:
	#return clsmembers

def printOnStatusBar(statusbar, data=None):
	""" Send data on status bar
	"""
	if not data: data = {}
	for k, v in data.items():
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
		cls = ("", "", "")

	### check cls error
	if isinstance(cls, tuple):
		return cls
	else:

		### check devs instance
		devs = Utilities.getInstance(cls, args)

		### check instance error
		return devs if isinstance(devs, tuple) else None

################################################################
#                                                              #
# 						GENERAL CLASS                          #
#                                                              #
################################################################



# Generic Shape Event Handler------------------------------------
class ShapeEvtHandler:
	""" Handler class
	"""

	def OnLeftUp(self, event):
		pass

	def OnLeftDown(self, event):
		pass

	def leftUp(self, event):
		pass

	def OnLeftDClick(self, event):
		pass

	def OnRightUp(self, event):
		pass

	def OnRightDown(self, event):
		pass

	def OnRightDClick(self, event):
		pass

	def OnSelect(self, event):
		pass

	def OnDeselect(self, event):
		pass

	def OnMove(self, event):
		pass

	def OnResize(self, event):
		pass

	def OnConnect(self, event):
		pass


# Generic Graphic items------------------------------------------
class Shape(ShapeEvtHandler):
	""" Shape class
	"""

	def __init__(self, x=None, y=None):
		""" Constructor
		"""
		if not y: y = []
		if not x: x = []

		self.x = array.array('d', x)                      # list of x coord
		self.y = array.array('d', y)                      # list of y coords
		self.fill = ['#add8e6']          # fill color
		self.pen = [self.fill[0], 1, wx.SOLID]   # pen color and size
		self.font = [FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, u'Arial']

	def draw(self, dc):
		""" Draw method
		"""

		r, g, b = Utilities.HEXToRGB(self.fill[0])
		brushclr = wx.Color(r, g, b, 128)   # half transparent

		try:
			dc.SetPen(wx.Pen(self.pen[0], self.pen[1], self.pen[2]))
		### for old model
		except:
			dc.SetPen(wx.Pen(self.pen[0], self.pen[1]))

		dc.SetBrush(wx.Brush(brushclr))

		try:
			dc.SetFont(wx.Font(self.font[0], self.font[1], self.font[2], self.font[3], False, self.font[4]))
		except Exception:
			try:
				dc.SetFont(wx.Font(10, self.font[1], self.font[2], self.font[3], False, self.font[4]))
			except Exception:
				dc.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, False, u'Arial'))

	def move(self, x, y):
		""" Move method
		"""
		if not self.lock_flag:
			self.x = array.array('d', map((lambda v: v + x), self.x))
			self.y = array.array('d', map((lambda v: v + y), self.y))

	def OnResize(self):
		""" Resize method controled by ResizeNode move method
		"""
		### dynamic font size with 1O (pointSize) * width (pourcent)/ 100
		self.font[0] = int(FONT_SIZE * (self.x[1] - self.x[0]) / 100.0)

	def lock(self):
		self.lock_flag = True

	def unlock(self):
		self.lock_flag = False

	def Copy(self):
		""" Function that return the deep copy of shape
		"""
		return copy.deepcopy(self)

#---------------------------------------------------------
class LineShape(Shape):
	"""
	"""

	def __init__(self, x1=20, y1=20, x2=50, y2=50):
		""" Cosntructor
		"""

		Shape.__init__(self, [x1, x2], [y1, y2])

	def draw(self, dc):
		""" Draw method
		"""

		Shape.draw(self, dc)
		dc.DrawLine(self.x[0], self.y[0], self.x[1], self.y[1])

	def HitTest(self, x, y):
		""" Hitest method
		"""
		if x < min(self.x) - 3: return False
		if x > max(self.x) + 3: return False
		if y < min(self.y) - 3: return False
		if y > max(self.y) + 3: return False

		top = (x - self.x[0]) * (self.x[1] - self.x[0]) + (y - self.y[0]) * (self.y[1] - self.y[0])
		distsqr = pow(self.x[0] - self.x[1], 2) + pow(self.y[0] - self.y[1], 2)
		u = float(top) / float(distsqr)

		newx = self.x[0] + u * (self.x[1] - self.x[0])
		newy = self.y[0] + u * (self.y[1] - self.y[0])

		dist = pow(pow(newx - x, 2) + pow(newy - y, 2), .5)

		return False if dist > 7 else True

#---------------------------------------------------------
class RoundedRectangleShape(Shape):
	"""     RoundedRectangleShape class
	"""

	def __init__(self, x1=20, y1=20, x2=120, y2=120):
		""" constructor
		"""
		Shape.__init__(self, [x1, x2], [y1, y2])

	def draw(self, dc):
		""" Draw method
		"""

		Shape.draw(self, dc)

		width, height = int(self.x[1] - self.x[0]), int(self.y[1] - self.y[0])
		x, y = int(self.x[0]), int(self.y[0])

		### Prepare label drawing
		rect = wx.Rect(x, y, width, height)
		r = 4.0
		dc.DrawRoundedRectangleRect(rect, r)

	#def GetRect(self):
	#width,height = int(self.x[1]-self.x[0]), int(self.y[1]-self.y[0])
	#return wx.Rect(self.x[0], self.y[0], width, height)

	def HitTest(self, x, y):
		""" Hitest method
		"""
		if x < self.x[0]: return False
		if x > self.x[1]: return False
		if y < self.y[0]: return False
		if y > self.y[1]: return False

		return True

#---------------------------------------------------------
class RectangleShape(Shape):
	""" RectangleShape class
	"""

	def __init__(self, x=20, y=20, x2=120, y2=120):
		""" Constructor
		"""

		Shape.__init__(self, [x, x2], [y, y2])

	def draw(self, dc):
		""" Draw paint method
		"""

		Shape.draw(self, dc)
		x, y = int(self.x[0]), int(self.y[0])
		width, height = int(self.x[1] - self.x[0]), int(self.y[1] - self.y[0])
		dc.DrawRectangle(x, y, width, height)

	def HitTest(self, x, y):
		""" Hitest method
		"""

		if x < self.x[0]: return False
		if x > self.x[1]: return False
		if y < self.y[0]: return False
		if y > self.y[1]: return False

		return True

#---------------------------------------------------------
class PolygonShape(Shape):
	""" PolygonShape class
	"""

	def __init__(self, x=20, y=20, x2=120, y2=120):
		""" Constructor
		"""

		Shape.__init__(self, [x, x2], [y, y2])

	def draw(self, dc):
		"""
		"""

		Shape.draw(self, dc)

		#  dx = (self.x[1] - self.x[0]) / 2
		dy = (self.y[1] - self.y[0]) / 2
		p0 = wx.Point(self.x[0], self.y[0] - dy / 2)
		p1 = wx.Point(self.x[0], self.y[1] + dy / 2)
		p2 = wx.Point(self.x[1], self.y[0] + dy)
		offsetx = (self.x[1] - self.x[0]) / 2

		dc.DrawPolygon((p0, p1, p2), offsetx)

	def HitTest(self, x, y):
		""" Hitest method
		"""

		if x < self.x[0]: return False
		if x > self.x[1]: return False
		if y < self.y[0]: return False
		if y > self.y[1]: return False
		return True

#---------------------------------------------------------
class CircleShape(Shape):
	def __init__(self, x=20, y=20, x2=120, y2=120, r=30.0):
		Shape.__init__(self, [x, x2], [y, y2])
		self.r = r

	def draw(self, dc):
		Shape.draw(self, dc)
		dc.SetFont(wx.Font(10, self.font[1], self.font[2], self.font[3], False, self.font[4]))
		dc.DrawCircle(int(self.x[0] + self.x[1]) / 2, int(self.y[0] + self.y[1]) / 2, self.r)
		dc.EndDrawing()

	def HitTest(self, x, y):
		if x < self.x[0]: return False
		if x > self.x[1]: return False
		if y < self.y[0]: return False
		if y > self.y[1]: return False
		return True

#---------------------------------------------------------
class PointShape(Shape):
	def __init__(self, x=20, y=20, size=4, type='rect'):
		Shape.__init__(self, [x], [y])
		self.type = type
		self.size = size

		if self.type == 'rondedrect':
			self.graphic = RoundedRectangleShape(x - size, y - size, x + size, y + size)
		elif self.type == 'rect':
			self.graphic = RectangleShape(x - size, y - size, x + size, y + size)
		elif self.type == 'circ':
			self.graphic = CircleShape(x - size, y - size, x + size, y + size, size)
		elif self.type == 'poly':
			self.graphic = PolygonShape(x - size, y - size, x + size, y + size)

		self.graphic.pen = self.pen
		self.graphic.fill = self.fill

	def moveto(self, x, y):
		self.x = x
		self.y = y
		size = self.size
		self.graphic.x = [x - size, x + size]
		self.graphic.y = [y - size, y + size]

	def move(self, x, y):
		self.x = array.array('d', map((lambda v: v + x), self.x))
		self.y = array.array('d', map((lambda v: v + y), self.y))
		self.graphic.move(x, y)

	def HitTest(self, x, y):
		return self.graphic.HitTest(x, y)

	def draw(self, dc):
		self.graphic.pen = self.pen
		self.graphic.fill = self.fill
		self.graphic.draw(dc)

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

		L = map(lambda a, b: (a, b), self.x, self.y)

		### update L depending of the connector type
		if ShapeCanvas.CONNECTOR_TYPE == 'linear':
			### line width
			w = self.x[1] - self.x[0]
			### left moving
			if w > 0:
				### output port
				if self.input:
					L.insert(1, (self.x[0] + w / 10, self.y[0]))
					L.insert(2, (self.x[1] - w / 10, self.y[1]))
				else:
					L.insert(1, (self.x[0] + w / 10, self.y[0]))
					L.insert(2, (self.x[1] - w / 10, self.y[1]))
			### right moving
			else:
				### output port
				if self.input:
					L.insert(1, (self.x[0] - w / 10, self.y[0]))
					L.insert(2, (self.x[1] - w / 10, self.y[1]))
				else:
					L.insert(1, (self.x[0] + w / 10, self.y[0]))
					L.insert(2, (self.x[1] + w / 10, self.y[1]))

		elif ShapeCanvas.CONNECTOR_TYPE == 'square':
			### line width
			w = self.x[1] - self.x[0]
			L.insert(1, (self.x[0] + w / 2, self.y[0]))
			L.insert(2, (self.x[0] + w / 2, self.y[1]))

		else:
			pass

		dc.DrawLines(L)

		### pour le rectangle en fin de connexion
		dc.DrawRectanglePointSize(wx.Point(self.x[-1] - 10 / 2, self.y[-1] - 10 / 2), wx.Size(10, 10))

	def HitTest(self, x, y):
		"""
		"""

		if x < min(self.x) - 3: return False
		if x > max(self.x) + 3: return False
		if y < min(self.y) - 3: return False
		if y > max(self.y) + 3: return False

		ind = 0
		try:
			while 1:
				x1 = self.x[ind]
				y1 = self.y[ind]
				x2 = self.x[ind + 1]
				y2 = self.y[ind + 1]

				top = (x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)
				distsqr = pow(x1 - x2, 2) + pow(y1 - y2, 2)
				u = float(top) / float(distsqr)

				newx = x1 + u * (x2 - x1)
				newy = y1 + u * (y2 - y1)

				dist = pow(pow(newx - x, 2) + pow(newy - y, 2), .5)

				if dist < 7:
					return True
				ind += 1

		except:
			pass

		return False

	def OnLeftDClick(self, event):
		"""
		"""

		### canvas containing LinesShape
		canvas = event.GetEventObject()
		### coordinates
		x, y = event.GetPositionTuple()
		### add point at the position according to the possible zoom (use of getScalledCoordinates)
		self.AddPoint(canvas.getScalledCoordinates(x, y))

	def HasPoint(self, point):
		"""
		"""

		x, y = point
		return (x in self.x) and (y in self.y)

	def AddPoint(self, point=(0, 0)):
		""" Add point under LineShape
		"""
		x, y = point

		# insertion sur les morceaux de droites d'affines
		for i in xrange(len(self.x) - 1):
			x1 = self.x[i]
			x2 = self.x[i + 1]

			y1 = self.y[i]
			y2 = self.y[i + 1]

			if (x1<=x<=x2 and y1<=y<=y2) or ((x1<=x<=x2 and y2<y<y1) or (x2<=x<=x1 and y1<=y<=y2) or (x2<=x<=x1 and y2<=y<=y1)):
				self.x.insert(i + 1, x)
				self.y.insert(i + 1, y)

				#### cassure des locks
				self.unlock()
				break

#---------------------------------------------------------
class ConnectionShape(LinesShape, Resizeable.Resizeable, Selectable.Selectable, Structurable.Structurable):
	""" ConnectionShape class
	"""


	def __init__(self):
		""" Constructor
		"""
		LinesShape.__init__(self, LineShape(0, 0, 1, 1))
		Resizeable.Resizeable.__init__(self)
		Structurable.Structurable.__init__(self)

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
			self.x[0], self.y[0] = self.input[0].getPort('output', self.input[1])

		if self.output:
			self.x[-1], self.y[-1] = self.output[0].getPort('input', self.output[1])

		LinesShape.draw(self, dc)

	def lock(self):
		"""
		"""

		if self.input and self.output:
			host1 = self.input[0]
			host2 = self.output[0]

			try:
				host1.lock()
			except:
				pass

			try:
				host2.lock()
			except:
				pass

	def unlock(self):
		"""
		"""

		if self.input and self.output:
			host1 = self.input[0]
			host2 = self.output[0]

			try:
				host1.unlock()
			except:
				pass

			try:
				host2.unlock()
			except:
				pass

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


###--------------------------------------------------------###
class FixedList(list):
	""" List with fixed size (for undo/redo)
	"""

	def __init__(self, size=5):
		list.__init__(self)
		self.__size = size

	def GetSize(self):
		return self.__size

	def append(self, v):
		if len(self) == self.GetSize():
			del self[0]

		self.insert(len(self), v)

#-------------------------------------------------------------
class Diagram(Savable.Savable, Structurable.Structurable):
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
	def makeDEVSGraph(diagram, D=None, type=object):
		""" Make a formated dictionnary to make the graph of the DEVS Network : {'S1': [{'C1': (1, 0)}, {'M': (0, 1)}], port 1 of S1 is connected to the port 0 of C1...
		"""
		if not D: D = {}


		# for all components in the diagram
		for c in diagram.GetShapeList():
			# if the component is the conncetionShape, then add the new element in the D dictionnary
			if isinstance(c, ConnectionShape):
				model1, portNumber1 = c.input
				model2, portNumber2 = c.output

				# return D with object representation
				if type is object:
					D.setdefault(model2, []).append({model1: (portNumber2, portNumber1)})

					if isinstance(model1, (iPort, oPort)):
						D.setdefault(model1, []).append({model2: (portNumber1, portNumber2)})

				# return D with string representation
				else:
					label1 = model1.label
					label2 = model2.label

					D.setdefault(label2, []).append({label1: (portNumber2, portNumber1)})

					if isinstance(model1, (iPort, oPort)):
						D.setdefault(label1, []).append({label2: (portNumber1, portNumber2)})

			#if the component is a container block achieve the recursivity
			elif isinstance(c, ContainerBlock):
				Diagram.makeDEVSGraph(c, D, type)

		return D

	@staticmethod
	def makeDEVSInstance(diagram=None):
		""" Return the DEVS instance of diagram. iterations order is very important !
		1. we make the codeblock devs instance
		2. we make the devs port instance for all devsimpy port
		3. we make Containerblock instance
		4. we make the connnection
		"""

		#ReloadModule.recompile("DomainInterface.DomainBehavior")
		#ReloadModule.recompile("DomainInterface.DomainStructure")
		### if devs instance of diagram is not instancied, we make it
		### else one simulation has been perfromed then we clear all devs port instances
		if diagram.getDEVSModel() is None:
			diagram.setDEVSModel(MasterModel.Master())
		else:
			diagram.ClearAllPorts()

		### shape list of diagram
		shape_list = diagram.GetShapeList()
		block_list = filter(lambda c: isinstance(c, Block), shape_list)

		### for all codeBlock shape, we make the devs instance
		for m in block_list:
			# creation des ports DEVS et des couplages pour la simulation

			cls = Components.GetClass(m.python_path)

			if isinstance(cls, (ImportError, tuple)):
				return _('Error making DEVS instances.\n %s' % (str(cls)))
			else:
				### recuperation du model DEVS
				devs = Utilities.getInstance(cls, m.args)

				### test if the instanciation is safe
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

			### adding
			diagram.addSubModel(devs)

			#### recursion
			if isinstance(m, ContainerBlock):
				Diagram.makeDEVSInstance(m)

		# for all iPort shape, we make the devs instance
		for m in filter(lambda s: isinstance(s, iPort), shape_list):
			diagram.addInPort()
			assert (len(diagram.getIPorts()) <= diagram.input)

		# for all oPort shape, we make the devs instance
		for m in filter(lambda s: isinstance(s, oPort), shape_list):
			diagram.addOutPort()
			assert (len(diagram.getOPorts()) <= diagram.output)

		### Connection
		for m in filter(lambda s: isinstance(s, ConnectionShape), shape_list):
			m1, n1 = m.input
			m2, n2 = m.output
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
				return _('Error making DEVS connection.\n Check your connections !')

			Structurable.Structurable.ConnectDEVSPorts(diagram, p1, p2)

		### change priority form priority_list is PriorityGUI has been invoked (Otherwise componentSet oreder is considered)
		diagram.updateDEVSPriorityList()

		return diagram.getDEVSModel()

	def SetParent(self, parent):
		# Todo : regler le probleme d'import
		# assert isinstance(parent, ShapeCanvas)
		self.parent = parent

	def GetParent(self):
		return self.parent

	def GetGrandParent(self):
		return self.GetParent().GetParent()

	@Decorators.cond_decorator(__builtin__.__dict__['GUI_FLAG'], Decorators.ProgressNotification("DEVSimPy open file"))
	def LoadFile(self, fileName=None):
		""" Function that load diagram from a file.
		"""

		load_file_result = Savable.Savable.LoadFile(self, fileName)

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

	#@Decorators.cond_decorator(__builtin__.__dict__['GUI_FLAG'], Decorators.StatusBarNotification('Load'))
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
		if not self.priority_list:
			self.priority_list = shapes_list
		else:

			### priority list manager
			cpt = 1
			lenght = len(shapes_list)
			result = [None] * lenght
			for s in shapes_list:
				if s in self.priority_list:
					try:
						result[self.priority_list.index(s)] = s
					except:
						pass
				else:
					result[lenght - cpt] = s
					cpt += 1

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
		msg += _("Number of atomic devs model: %d\n") % stat_dico['Atomic_nbr']
		msg += _("Number of coupled devs model: %d\n") % stat_dico['Coupled_nbr']
		msg += _("Number of coupling: %d\n") % stat_dico['Connection_nbr']
		msg += _("Number of deep level (description hierarchie): %d\n") % stat_dico['Deep_level']

		dlg = wx.lib.dialogs.ScrolledMessageDialog(self.GetParent(), msg, _("Diagram Information"))
		dlg.ShowModal()

	def OnClosePriorityGUI(self, event):
		""" Method that update the self.priority_list and close the priorityGUI Frame
		"""

		obj = event.GetEventObject()
		self.priority_list = [obj.listCtrl.GetItemText(i) for i in xrange(obj.listCtrl.GetItemCount())]
		obj.Destroy()

		### we can udpate the devs priority list during the simulation ;-)
		self.updateDEVSPriorityList()

	def OnAddConstants(self, event):
		""" Method that add constant parameters in order to simplify the modling codeBlock model
		"""

		obj = event.GetEventObject()

		### conditionnal statement only for windows
		win = obj.GetInvokingWindow() if isinstance(obj, wx.Menu) else obj

		### event come from right clic on the shapecanvas
		if isinstance(win, ShapeCanvas):
			win = win.GetParent()
			if isinstance(win, DetachedFrame):
				title = win.GetTitle()
			else:
				title = win.GetPageText(win.GetSelection())
		### event come from Main application by the Diagram menu
		else:
			nb2 = win.GetDiagramNotebook()
			title = nb2.GetPageText(nb2.GetSelection())

		dlg = DiagramConstantsDialog.DiagramConstantsDialog(win, wx.ID_ANY, title, self)
		dlg.ShowModal()
		dlg.Destroy()

	@Decorators.BuzyCursorNotification
	def checkDEVSInstance(self, diagram=None, D=None):
		""" Recursive DEVS instance checker for a diagram.

			@param diagram : diagram instance
			@param D : Dictionary of models with the associated error

		"""
		if not D: D = {}
		### shape list of diagram
		shape_list = diagram.GetShapeList()

		#### for all codeBlock and containerBlock shapes, we make the devs instance
		for m in filter(lambda s: isinstance(s, (CodeBlock, ContainerBlock)), shape_list):
			D[m] = CheckClass(m)
			## for all ContainerBlock shape, we make the devs instance and call the recursion
			if isinstance(m, ContainerBlock):
				self.checkDEVSInstance(m, D)

	def DoCheck(self):
		""" Ckeck all models for validation
			Return None if all models are ok, D else
		"""
		### dictionary composed by key = label of model and value = None if no error, exc_info() else
		D = {}
		self.checkDEVSInstance(self, D)
		return D if filter(lambda m: m != None, D.values()) != [] else None
	def OnCheck(self, event):
		""" Check button has been clicked. We chek if models which compose the diagram are valide.
		"""
		### if there are models in diagram
		if self.GetCount() != 0:

            # window that contain the diagram which will be simulate
			#mainW = wx.GetApp().GetTopWindow()
			#win = mainW.GetWindowByEvent(event)




			obj = event.GetEventObject()
			win = obj.GetTopLevelParent()

			D = self.DoCheck()
            ### if there is no error

 			if D is None:
				dial = wx.MessageDialog(win,
										_('All DEVS model has been instanciated without error.\n\nDo you want simulate ?'),
										_('Error Manager'),
										wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)

				if dial.ShowModal() == wx.ID_YES:
					self.OnSimulation(event)
			else:
				frame = CheckerGUI.CheckerGUI(win, D)
				frame.Show()

		### no modles in diagram
		else:
			wx.MessageBox(_("Diagram is empty.\n\nPlease, drag-and-drop model from libraries control panel to build a diagram."),_('Error Manager'))
	def OnSimulation(self, event):
		"""Method calling the simulationGUI
		"""


        ### if there are models in diagram
		if self.GetCount() != 0 :
			## window that contain the diagram which will be simulate
			# mainW = wx.GetApp().GetTopWindow()
			# window = Utilities.GetActiveWindow()

			# diagram which will be simulate
			diagram = self

			D = self.DoCheck()
			### if there is no error in models
 			if D is not None:
				Utilities.playSound(SIMULATION_ERROR_SOUND_PATH)

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
				if len(L) != len(set(L)):
					wx.MessageBox(_("It seems that models have same label.\nIf you plan to use Flat simulation algorithm, all model must have a unique label."), _("Simulation Manager"))

				# set the name of diagram from notebook nb2
				nb2 = win.GetDiagramNotebook()
				title = window.GetTitle() if isinstance(window, DetachedFrame.DetachedFrame) else nb2.GetPageText(nb2.GetSelection()).rstrip()
				diagram.label = os.path.splitext(os.path.basename(title))[0]

				## delete all attached devs instances
				diagram.Clean()

				## make DEVS instance from diagram
				master = Diagram.makeDEVSInstance(diagram)

				if all(model.bad_filename_path_flag for model in filter(lambda m: isinstance(m, Block),diagram.GetShapeList()) if hasattr(model, 'bad_filename_path_flag')):
					dial = wx.MessageDialog(window, _("You dont make the simulation of the Master model.\nSome models have bad fileName path !"), _('Simulation Manager'), wx.OK | wx.ICON_EXCLAMATION)
					dial.ShowModal()
					return False
				else:

					# pluginmanager.trigger_event('START_DIAGRAM', parent=win, diagram=diagram)

					### clear all log file
					for fn in filter(lambda f: f.endswith('.devsimpy.log'), os.listdir(gettempdir())):
						os.remove(os.path.join(gettempdir(), fn))

					# obj = event.GetEventObject()
					# si invocation a partir du bouton dans la toolBar (apparition de la frame de simulation dans une fenetre)
					if isinstance(obj, wx.ToolBar) or 'Diagram' in obj.GetTitle():
						frame = SimulationGUI.SimulationDialog(win, wx.ID_ANY, _(" %s Simulator" % diagram.label), master)
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
						nb1.InsertPage(2, win.panel3, _("Simulation"), imageId=2)
					else:
						sys.stdout.write(_("This option has not been implemented yet."))
						return False

				return True
		else:
			wx.MessageBox(_("Diagram is empty. \nPlease, drag-and-drop model from libraries control panel to build a diagram."),_('Simulation Manager'))
			return False

	def AddShape(self, shape, after=None):
		""" Method that insert shape into the diagram at the position 'after'
		"""

		index = self.shapes.index(after) if after else 0
		self.UpdateAddingCounter(shape)
		self.InsertShape(shape, index)

	def InsertShape(self, shape, index=0):
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
				if shape in cs.input + cs.output:
					self.shapes.remove(cs)

		if isinstance(shape, Block):
			if shape.label in self.priority_list:
				### update priority list
				self.priority_list.remove(shape.label)

		try:
			### delete shape
			self.shapes.remove(shape)
		except ValueError:
			sys.stdout.write(_("Error trying to remove %s") % shape)

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
			self.nbCodeBlock -= 1
		elif isinstance(shape, ContainerBlock):
			self.deletedContainerBlockId.append(shape.id)
			self.nbContainerBlock -= 1
		elif isinstance(shape, iPort):
			self.deletediPortId.append(shape.id)
			self.nbiPort -= 1
		elif isinstance(shape, oPort):
			self.deletedoPortId.append(shape.id)
			self.nboPort -= 1
		else:
			pass

	def UpdateAddingCounter(self, shape):
		""" Method that update the added shape counter
		"""

		# gestion du nombre de shape
		if isinstance(shape, CodeBlock):
			shape.id = self.GetCodeBlockCount()
			self.nbCodeBlock += 1
		elif isinstance(shape, ContainerBlock):
			shape.id = self.GetContainerBlockCount()
			self.nbContainerBlock += 1
		elif isinstance(shape, iPort):
			self.nbiPort += 1
		elif isinstance(shape, oPort):
			self.nboPort += 1
		else:
			pass

	def update(self, concret_subject=None):
		""" Update method is invoked by notify method of Subject class
		"""

		### update shapes list in diagram with a delete of connexionShape which no longer exists (when QuickAttributeEditor change input or output of Block)
		csList = filter(lambda a: isinstance(a, ConnectionShape), self.shapes)

		for cs in csList:
			index = cs.output[1]
			model = cs.output[0]
			### if index+1 is superiror to the new number of port (model.input)
			if index + 1 > model.input:
				self.DeleteShape(cs)

			index = cs.input[1]
			model = cs.input[0]
			### if index+1 is superiror to the new number of port (model.output)
			if index + 1 > model.output:
				self.DeleteShape(cs)

	def PopShape(self, index=-1):
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
		self.shapes.insert(pos, shape)

	def GetCount(self):
		""" Function that return the number of shapes that composed the diagram
		"""

		return len(self.shapes)

	def GetFlatBlockShapeList(self, l=None):
		""" Get the flat list of Block shape using recursion process
		"""
		if not l: l = []

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

		# sys.stderr.write(_("Block %s not found.\n" % label))
		return False

	def GetShapeList(self):
		""" Function that return the shapes list
		"""

		return self.shapes

	def GetBlockCount(self):
		""" Function that return the number of Block shape
		"""

		return self.GetCodeBlockCount() + self.GetContainerBlockCount()

	def GetCodeBlockCount(self):
		""" Function that return the number of codeBlock shape
		"""

		if self.deletedCodeBlockId:
			return self.deletedCodeBlockId.pop()
		else:
			return self.nbCodeBlock

	def GetContainerBlockCount(self):
		""" Function that return the number of containerBlock shape
		"""

		if self.deletedContainerBlockId:
			return self.deletedContainerBlockId.pop()
		else:
			return self.nbContainerBlock

	def GetiPortCount(self):
		""" Function that return the number of iPort shape
		"""

		if self.deletediPortId:
			return self.deletediPortId.pop()
		else:
			return self.nbiPort

	def GetoPortCount(self):
		""" Function that return the number of oPort shape
		"""

		if self.deletedoPortId:
			return self.deletedoPortId.pop()
		else:
			return self.nboPort

	def Clean(self):
		""" Clean DEVS instances attached to all block model in the diagram.
		"""

		try:

			for devs in filter(lambda a: hasattr(a, 'finish'), self.devsModel.componentSet):
				Publisher.unsubscribe(devs.finish, "%d.finished" % (id(devs)))

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

	def GetStat(self, d=None):
		""" Get information about diagram like the numbe rof atomic model or the number of link between models.
		"""
		if not d: d = {'Atomic_nbr': 0, 'Coupled_nbr': 0, 'Connection_nbr': 0, 'Deep_level': 0}

		first_coupled = False
		for m in self.GetShapeList():
			if isinstance(m, CodeBlock):
				d['Atomic_nbr'] += 1
			elif isinstance(m, ContainerBlock):
				d['Coupled_nbr'] += 1
				if not first_coupled:
					first_coupled = True
					d['Deep_level'] += 1
				m.GetStat(d)
			elif isinstance(m, ConnectionShape):
				d['Connection_nbr'] += 1

		return d

	def GetLabelList(self, l=None):
		""" Get Labels of all models
		"""
		if not l: l = []

		for m in self.GetShapeList():
			if isinstance(m, CodeBlock):
				l.append(m.label)
			elif isinstance(m, ContainerBlock):
				l.append(m.label)
				m.GetLabelList(l)
		return l


#Basic Graphical Components---------------------------------------------------------
class Block(RoundedRectangleShape, Connectable.Connectable, Resizeable.Resizeable, Selectable.Selectable,
			Attributable.Attributable, Rotable.Rotable, Plugable.Plugable, Observer.Observer, Testable.Testable,
			Savable.Savable):
	""" Generic Block class.
	"""

	def __init__(self, label='Block', nb_inputs=1, nb_outputs=1):
		""" Constructor
		"""

		RoundedRectangleShape.__init__(self)
		Resizeable.Resizeable.__init__(self)
		Connectable.Connectable.__init__(self, nb_inputs, nb_outputs)
		Attributable.Attributable.__init__(self)
		Selectable.Selectable.__init__(self)

		self.AddAttributes(Attributable.Attributable.GRAPHICAL_ATTR)
		self.label = label
		self.label_pos = 'center'
		self.image_path = ""
		self.id = 0
		self.nb_copy = 0        # nombre de fois que le bloc est copie (pour le label des blocks copies
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
		mx = int((self.x[0] + self.x[1])/2.0)-int(w/2.0)
		
		if self.label_pos == 'bottom':
			### bottom
			my = int(self.y[1]-h)
		elif self.label_pos == 'top':
			### top
			my = int(self.y[0]+h/2.0)
		else:
			my = int((self.y[0] + self.y[1])/2.0)-int(h/2.0)
			
		### with and height of rectangle
		self.w = self.x[1] - self.x[0]
		self.h = self.y[1] - self.y[0]

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
			img = wx.Bitmap(os.path.join(ICON_PATH_16_16, 'lock.png'), wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap(img, self.x[0], self.y[0])

		### Draw filename path flag picture
		if self.bad_filename_path_flag:
			img = wx.Bitmap(os.path.join(ICON_PATH_16_16, 'flag_exclamation.png'), wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap(img, self.x[0] + 15, self.y[0])

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
		Selectable.Selectable.ShowAttributes(self, event)
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
		f = PluginsGUI.ModelPluginsManager(parent=canvas.GetParent(),
										   id=wx.ID_ANY,
										   title =_('%s - plugin manager')%self.label,
										   size=(700, 500),
										   style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN,
										   model=self)
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
		menuItem = menu.FindItemById(itemId)
		ext = menuItem.GetLabel().lower()

		wcd = _('%s Files (*.%s)|*.%s|All files (*)|*') % (ext.upper(), ext, ext)
		save_dlg = wx.FileDialog(parent,
								 message=_('Export file as...'),
								 defaultDir=domain_path,
								 defaultFile=str(self.label) + '.%s' % ext,
								 wildcard=wcd,
								 style=wx.SAVE | wx.OVERWRITE_PROMPT)

		if save_dlg.ShowModal() == wx.ID_OK:
			path = os.path.normpath(save_dlg.GetPath())
			label = os.path.basename(path)
			try:
				### Block is Savable
				self.SaveFile(path)

				printOnStatusBar(mainW.statusbar, {0: _('%s Exported') % label, 1: ''})

			except IOError, error:
				dlg = wx.MessageDialog(parent, _('Error exported file %s\n') % error, label, wx.ID_OK | wx.ICON_ERROR)
				dlg.ShowModal()

		save_dlg.Destroy()

	def update(self, concret_subject=None):
		"""
		"""

		state = concret_subject.GetState()

		### for all properties
		for prop in state:
			val = state[prop]

			# if behavioral propertie
			if prop in self.args:
				self.args[prop] = val
				# si attribut comportemental definit
				# (donc au moins une simulation sur le modele, parce que les instances DEVS ne sont faites qu'a la simulation)
				# alors on peut mettre a jour dynamiquement pendant la simulation :-)
				# attention necessite une local copy dans le constructeur des model DEVS (generalement le cas lorsqu'on veux reutiliser les param du constructeur dans les methodes)
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
				if val not in ('', [], {}) or (prop == 'image_path' and val == ""):
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
		s = _("\t Label: %s\n") % self.label
		s += "\t Input/Output: %s,%s\n" % (str(self.input), str(self.output))
		return s

#---------------------------------------------------------
class CodeBlock(Block, Achievable.Achievable):
	""" CodeBlock(label, inputs, outputs)
	"""

	###
	def __init__(self, label='CodeBlock', nb_inputs=1, nb_outputs=1):
		""" Constructor.
		"""
		Block.__init__(self, label, nb_inputs, nb_outputs)
		Achievable.Achievable.__init__(self)

	###
	def __setstate__(self, state):
		""" Restore state from the unpickled state values.
		"""

		python_path = state['python_path']
		model_path = state['model_path']

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
					
					path = os.path.join(os.path.dirname(DOMAIN_PATH), Utilities.relpath(str(model_path[model_path.index(dir_name):]).strip('[]')))

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
						### we find the python file using re module because path can comes from windows and then sep is not the same and os.path.basename don't work !
						state['python_path'] = os.path.join(path, re.findall("([\w]*[%s])*([\w]*.py)"%os.sep, python_path)[0][-1])
						
				else:
					state['bad_filename_path_flag'] = True
			
			### load enventual Plugin
			if 'plugins' in state:
				wx.CallAfter(self.LoadPlugins, (state['model_path']))

		### if the model path is empty and the python path is wrong
		elif not os.path.exists(python_path):
			### if DOMAIN is not in python_path
			if dir_name in python_path:

				path = os.path.join(os.path.dirname(DOMAIN_PATH), Utilities.relpath(str(python_path[python_path.index(dir_name):]).strip('[]')))

				### try to find it in exportedPathList (after Domain check)
				if not os.path.exists(path):
					mainW = wx.GetApp().GetTopWindow()
					for p in mainW.exportPathsList:
						lib_name = os.path.basename(p)
						if lib_name in path:
							path = p + path.split(lib_name)[-1]
							break

				### if path is always wrong, flag is visible
				if not os.path.exists(path):
					state['bad_filename_path_flag'] = True
				else:
					state['python_path'] = path
			else:
				state['bad_filename_path_flag'] = True

		### test if args from construcor in python file stored in library (on disk) and args from stored model in dsp are the same
		if os.path.exists(python_path) or zipfile.is_zipfile(os.path.dirname(python_path)):
			args_from_stored_constructor_py = inspect.getargspec(cls.__init__).args[1:]
			args_from_stored_block_model = state['args']
			L = list(set(args_from_stored_constructor_py).symmetric_difference(set(args_from_stored_block_model)))
			if L:
				for arg in L:
					if not arg in args_from_stored_constructor_py:
						sys.stdout.write(_("Warning: %s come is old ('%s' arg is deprecated). We update it...\n" % (state['python_path'], arg)))
						del state['args'][arg]
					else:
						arg_values = inspect.getargspec(cls.__init__).defaults
						index = args_from_stored_constructor_py.index(arg)
						state['args'].update({arg: arg_values[index]})
			else:
				sys.stderr.write(_("Error in setstate for CodeBlock: %s\n"%str(cls)))

		### if the fileName attribut dont exist, we define it into the current devsimpy directory (then the user can change it from Property panel)
		if 'args' in state:
			### find all word containning 'filename' without considering the casse
			m = [re.match('[a-zA-Z]*filename[_-a-zA-Z0-9]*', s, re.IGNORECASE) for s in state['args'].keys()]
			filename_list = map(lambda a: a.group(0), filter(lambda s: s is not None, m))
			### for all filename attr
			for name in filename_list:
				fn = state['args'][name]
				if not os.path.exists(fn):
					### try to redefine the path
					if dir_name in fn:
						fn = os.path.join(HOME_PATH, Utilities.relpath(str(fn[fn.index(dir_name):]).strip('[]')))
					else:
						fn = os.path.join(HOME_PATH, fn_bn)

					### show flag icon on the block anly for the file with extension (input file)
					if os.path.splitext(fn)[-1] != '':
						state['bad_filename_path_flag'] = True

					state['args'][name] = fn

		####################################" Just for old model
		if 'bad_filename_path_flag' not in state: state['bad_filename_path_flag'] = False
		if 'lock_flag' not in state: state['lock_flag'] = False
		if 'image_path' not in state:
			state['image_path'] = ""
			state['attributes'].insert(3, 'image_path')
		if 'font' not in state:
			state['font'] = [FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, u'Arial']
		if 'font' not in state['attributes']:
			state['attributes'].insert(3, 'font')
		if 'selected' not in state: state['selected'] = False
		if 'label_pos' not in state: state['label_pos'] = 'center'
		##############################################

		#print "apres "
		#print state['python_path']
		#print state['model_path']
		#print "\n"

		self.__dict__.update(state)

	def __getstate__(self):
		"""
		"""
		"""Return state values to be pickled."""
		return Achievable.Achievable.__getstate__(self)

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
			dc.DrawBitmap(img, self.x[1] - 20, self.y[0])

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

	def update(self, concret_subject=None):
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
					m = [re.match('[a-zA-Z_]*ilename[_-a-zA-Z0-9]*', prop, re.IGNORECASE)]
					filename_list = map(lambda a: a.group(0), filter(lambda s: s is not None, m))
					### for all filename attr
					for name in filename_list:
						val = state[prop]
						# if behavioral propertie
						if prop in self.args:
							### is abs fileName ?
							if os.path.isabs(val):
								### if there is an extention, then if the field path exist we color in red and update the bad_filename_path_flag
								bad_flag_dico.update({prop: not os.path.exists(val) and os.path.splitext(val)[-1] == ''})

				self.bad_filename_path_flag = True in bad_flag_dico.values()

	###
	def __repr__(self):
		""" Text representation.
		"""
		s = Block.__repr__(self)
		s += "\t DEVS module path: %s \n" % str(self.python_path)
		s += "\t DEVSimPy model path: %s \n" % str(self.model_path)
		s += "\t DEVSimPy image path: %s \n" % str(self.image_path)
		return s

#---------------------------------------------------------
class ContainerBlock(Block, Diagram, Structurable.Structurable):
	""" ContainerBlock(label, inputs, outputs)
	"""

	###
	def __init__(self, label='ContainerBlock', nb_inputs=1, nb_outputs=1):
		""" Constructor
		"""
		Block.__init__(self, label, nb_inputs, nb_outputs)
		Diagram.__init__(self)
		Structurable.Structurable.__init__(self)
		self.fill = ['#90ee90']

	###
	def __setstate__(self, state):
		""" Restore state from the unpickled state values.
		"""

		python_path = state['python_path']
		model_path = state['model_path']

		#print "avant "
		#print state['python_path']
		#print state['model_path']
		#print "\n"

		dir_name = os.path.basename(DOMAIN_PATH)
		### if the model path is wrong
		if model_path != '':
			if not os.path.exists(model_path):
				### try to find it in the Domain (firstly)
				if dir_name in python_path:
					path = os.path.join(os.path.dirname(DOMAIN_PATH), Utilities.relpath(str(model_path[model_path.index(dir_name):]).strip('[]')))

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
					L = list(set(args_from_stored_constructor_py).symmetric_difference(set(args_from_stored_block_model)))
					if L:
						for arg in L:
							if not arg in args_from_stored_constructor_py:
								sys.stdout.write(_("Warning: %s come is old ('%s' arg is deprecated). We update it...\n" % (state['python_path'], arg)))
								del state['args'][arg]
							else:
								arg_values = inspect.getargspec(cls.__init__).defaults
								index = args_from_stored_constructor_py.index(arg)
								state['args'].update({arg: arg_values[index]})
				else:
					sys.stderr.write(_("Error in setstate for ContainerBlock: %s\n"%str(cls)))

		### if the model path is empty and the python path is wrong
		elif not os.path.exists(python_path):
			if dir_name in python_path:
				path = os.path.join(os.path.dirname(DOMAIN_PATH), Utilities.relpath(str(python_path[python_path.index(dir_name):]).strip('[]')))
				state['python_path'] = paths

				if not os.path.exists(path):
					state['bad_filename_path_flag'] = True

		####################################" Just for old model
		if 'bad_filename_path_flag' not in state: state['bad_filename_path_flag'] = False
		if 'lock_flag' not in state: state['lock_flag'] = False
		if 'parent' not in state: state['parent'] = None
		if 'image_path' not in state:
			state['image_path'] = ""
			state['attributes'].insert(3, 'image_path')
		if 'font' not in state:
			state['font'] = [FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, u'Arial']
		if 'font' not in state['attributes']:
			state['attributes'].insert(3, 'font')
		if 'selected' not in state: state['selected'] = False
		if 'label_pos' not in state: state['label_pos'] = 'center'
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
			return ['shapes', 'priority_list', 'constants_dico', 'model_path', 'python_path', 'args'] + self.GetAttributes()
		else:
			raise AttributeError, name

	def draw(self, dc):

		if self.selected:
			### inform about the nature of the block using icon
			img = wx.Bitmap(os.path.join(ICON_PATH_16_16, 'coupled3.png'), wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap(img, self.x[1] - 20, self.y[0])

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

		frame = DetachedFrame(parent=mainW, title=self.label, diagram=self, name=self.label)
		frame.SetIcon(mainW.GetIcon())
		frame.Show()

	def __repr__(self):
		s = Block.__repr__(self)
		s += _("\t DEVS module: %s \n" % str(self.python_path))
		s += "\t DEVSimPy model path: %s \n" % str(self.model_path)
		s += "\t DEVSimPy image path: %s \n" % str(self.image_path)
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

		self.item = item    ### parent Block
		self.index = index    ### number of port
		self.cf = cf        ### parent canvas
		self.label = ""

		self.lock_flag = False                  # move lock
		PointShape.__init__(self, type=t)

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
		Node.__init__(self, item, index, cf, t='circ')

	def OnLeftDown(self, event):
		""" Left Down clic has been invoked
		"""
		### deselect the block to delete the info flag
		self.cf.deselect(self.item)
		event.Skip()

	def HitTest(self, x, y):
		""" Collision detection method
		"""

		### old model can produce an error
		try:
			r = self.graphic.r
			xx = self.x[0] if isinstance(self.x, array.array) else self.x
			yy = self.y[0] if isinstance(self.y, array.array) else self.y

			return not ((x < xx - r or x > xx + r) or (y < yy - r or y > yy + r))
		except Exception, info:
			sys.stdout.write(_("Error in Hitest for %s : %s\n") % (self, info))
			return False

class INode(ConnectableNode):
	""" INode(item, index, cf)
	"""

	def __init__(self, item, index, cf):
		""" Constructor.
		"""
		ConnectableNode.__init__(self, item, index, cf)

		self.label = "in%d"%self.index
		
	def move(self, x, y):
		""" Move method
		"""
		self.cf.deselect()
		ci = ConnectionShape()
		ci.setOutput(self.item, self.index)
		ci.x[0], ci.y[0] = self.item.getPort('input', self.index)
		self.cf.diagram.shapes.insert(0, ci)
		self.cf.showOutputs()
		self.cf.select(ci)

	def leftUp(self, items):
		""" Left up action has been invocked
		"""

		cs = items[0]

		#if self.item in cs.touch_list:
			#index = cs.touch_list.index(self.item)
			#del cs.touch_list[index]

		if len(items) == 1 and isinstance(cs, ConnectionShape) and cs.output is None:
			cs.setOutput(self.item, self.index)
		#cs.ChangeForm(ShapeCanvas.CONNECTOR_TYPE)


	def draw(self, dc):
		""" Drawing method
		"""
		x, y = self.item.getPort('input', self.index)
		self.moveto(x, y)

		self.fill = ['#00b400'] #GREEN

		### prot number
		dc.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL))
		#dc.SetPen(wx.Pen(wx.NamedColour('black'), 20))
		dc.DrawText(str(self.index), self.x - self.graphic.r, self.y - self.graphic.r - 2)

		### position of label
		if not isinstance(self.item, Port):
			### perapre label position
			if self.item.direction == 'ouest':
				xl = x-30
				yl = y
			elif self.item.direction == 'est':
				xl = x+2			
				yl = y
			elif self.item.direction == 'nord':
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
		""" Moving method
		"""
		self.cf.deselect()
		ci = ConnectionShape()
		ci.setInput(self.item, self.index)
		ci.x[1], ci.y[1] = self.item.getPort('output', self.index)
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
		x, y = self.item.getPort('output', self.index)
		self.moveto(x, y)
		self.fill = ['#ff0000']

		### prot number
		dc.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL))
		#dc.SetPen(wx.Pen(wx.NamedColour('black'), 20))
		dc.DrawText(str(self.index), self.x - self.graphic.r, self.y - self.graphic.r - 2)

		### position of label
		if not isinstance(self.item, Port):
			### perapre label position
			if self.item.direction == 'ouest':
				xl = x+2
				yl = y
			elif self.item.direction == 'est':
				xl = x-30
				yl = y
			elif self.item.direction == 'nord':
				xl = x
				yl = y+2
			else:
				xl = x
				yl = y-18
			
			### Draw label above port
			dc.DrawText(self.label, xl, yl)
		
		### Drawing
		PointShape.draw(self, dc)

###
class ResizeableNode(Node):
	""" Resizeable(item, index, cf, type)
	"""

	def __init__(self, item, index, cf, t='rect'):
		""" Constructor.
		"""
		Node.__init__(self, item, index, cf, t)

		self.fill = ['#000000'] #BLACK

	def draw(self, dc):
		""" Drawing method
		"""

		try:
			self.moveto(self.item.x[self.index], self.item.y[self.index])
		except IndexError:
			pass

		PointShape.draw(self, dc)

	def move(self, x, y):
		""" moving method
		"""

		lines_shape = self.item

		if self.index == 0:
			X = abs(self.item.x[1] - self.item.x[0] - x)
			Y = abs(self.item.y[1] - self.item.y[0] - y)
		else:
			X = abs(self.item.x[1] + x - self.item.x[0])
			Y = abs(self.item.y[1] + y - self.item.y[0])

		### if no lock
		if not lines_shape.lock_flag:
			### Block and minimal size (50,50) or not Block
			if (isinstance(self.item, Block) and X >= 50 and Y >= 50) or not isinstance(self.item, Block):
				self.item.x[self.index] += x
				self.item.y[self.index] += y
				self.item.OnResize()

	def OnDeleteNode(self, event):
		if isinstance(self.item, ConnectionShape):
			for x in self.item.x:
				if x - 3 <= event.GetX() <= x + 3:
					y = self.item.y[self.item.x.index(x)]
					if y - 3 <= event.GetY() <= y + 3:
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
class Port(CircleShape, Connectable.Connectable, Selectable.Selectable, Attributable.Attributable, Rotable.Rotable, Observer.Observer):
	""" Port(x1,y1, x2, y2, label)
	"""

	def __init__(self, x1, y1, x2, y2, label='Port'):
		""" Constructor.
		"""

		CircleShape.__init__(self, x1, y1, x2, y2, 30.0)
		Connectable.Connectable.__init__(self)
		Attributable.Attributable.__init__(self)

		self.AddAttributes(Attributable.Attributable.GRAPHICAL_ATTR[0:4])
		self.label = label
		self.id = 0
		self.args = {}
		self.lock_flag = False                  # move lock

	def __setstate__(self, state):
		""" Restore state from the unpickled state values.
		"""


		####################################" Just for old model
		if 'r' not in state: state['r'] = 30.0
		if 'font' not in state: state['font'] = [FONT_SIZE, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, u'Arial']
		##############################################

		self.__dict__.update(state)

	def draw(self, dc):
		CircleShape.draw(self, dc)
		w, h = dc.GetTextExtent(self.label)


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
			img = wx.Bitmap(os.path.join(ICON_PATH_16_16, 'lock.png'), wx.BITMAP_TYPE_ANY)
			dc.DrawBitmap(img, self.x[0] + w / 3, self.y[0])

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
		Selectable.Selectable.ShowAttributes(self, event)
		event.Skip()

	def OnProperties(self, event):
		"""
		"""
		canvas = event.GetEventObject()
		f = AttributeEditor(canvas.GetParent(), wx.ID_ANY, self, canvas)
		f.Show()

	###
	def OnLeftDClick(self, event):
		"""
		"""
		self.OnProperties(event)

	def update(self, concret_subject=None):
		"""
		"""
		state = concret_subject.GetState()

		for prop in state:
			val = state[prop]
			canvas = concret_subject.canvas
			if val != getattr(self, prop):
				setattr(self, prop, val)
				canvas.UpdateShapes([self])

	def __repr__(self):
		s = "\t Label: %s\n" % self.label
		return s

#------------------------------------------------------------------
class iPort(Port):
	""" IPort(label)
	"""

	def __init__(self, label='iPort'):
		""" Constructor
		"""

		Port.__init__(self, 50, 60, 100, 120, label)
		self.fill = ['#add8e6']          # fill color
		self.AddAttribute('id')
		self.label_pos = 'bottom'
		self.input = 0
		self.output = 1

	def getDEVSModel(self):
		return self

	def setDEVSModel(self, devs):
		self = devs

	def __repr__(self):
		s = Port.__repr__(self)
		s += "\t id: %d \n" % self.id
		return s

#----------------------------------------------------------------
class oPort(Port):
	""" OPort(label)
	"""

	def __init__(self, label='oPort'):
		""" Construcotr
		"""

		Port.__init__(self, 50, 60, 100, 120, label)
		self.fill = ['#90ee90']
		self.AddAttribute('id')
		self.label_pos = 'bottom'
		self.input = 1
		self.output = 0

	def getDEVSModel(self):
		return self

	def setDEVSModel(self, devs):
		self = devs

	def __repr__(self):
		s = Port.__repr__(self)
		s += "\t id: %d \n" % self.id
		return s

#--------------------------------------------------
class ScopeGUI(CodeBlock):
	""" ScopeGUI(label)
	"""

	def __init__(self, label='QuickScope'):
		""" Constructor
		"""

		CodeBlock.__init__(self, label, 1, 0)

		### enable edition on properties panel
		self.AddAttribute("xlabel")
		self.AddAttribute("ylabel")

	def OnLeftDClick(self, event):
		""" Left Double Click has been appeared.
		"""

		canvas = event.GetEventObject()

		# If the frame is call before the simulation process, the atomicModel is not instanciate (Instanciation delegate to the makeDEVSconnection after the run of the simulation process)
		devs = self.getDEVSModel()
		if devs is None:
			dial = wx.MessageDialog(None, _('No data available. \n\nGo to the simulation process first !'), self.label, wx.OK | wx.ICON_INFORMATION)
			dial.ShowModal()
		else:
			# Call the PlotManager which plot on the canvas depending the atomicModel.fusion option
			PlotGUI.PlotManager(canvas, self.label, devs, self.xlabel, self.ylabel)

#------------------------------------------------
class DiskGUI(CodeBlock):
	""" DiskGUI(label)
	"""

	def __init__(self, label='DiskGUI'):
		""" Constructor
		"""
		CodeBlock.__init__(self, label, 1, 0)

	def OnLeftDClick(self, event):
		"""
		"""
		devs = self.getDEVSModel()

		if devs is not None:
			mainW = wx.GetApp().GetTopWindow()
			frame = SpreadSheet.Newt(mainW, wx.ID_ANY, _("SpreadSheet %s") % self.label, devs, devs.comma if hasattr(devs, 'comma') else " ")
			frame.Center()
			frame.Show()
		else:
			dial = wx.MessageDialog(None, _('No data available \n\nGo to the simulation process first!'), self.label, wx.OK | wx.ICON_INFORMATION)
			dial.ShowModal()
