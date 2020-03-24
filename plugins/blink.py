# -*- coding: utf-8 -*-

"""
	Authors: L. Capocchi (capocchi@univ-corse.fr), C. Nicolai
	Date: 21/10/2010
	Description:
		Atomic models blink when there external or internal function are invoked.
		Moreover, this plug-ins allows you the step by step simulation.
		Warning: the module is enabled when the run button is pressed.
	Depends: Nothing
"""

import wx
import os
import sys
import pluginmanager

from types import MethodType

from Container import DetachedFrame, ConnectionShape, CodeBlock, ContainerBlock
from FindGUI import FindReplace
from Utilities import MoveFromParent
from Patterns.Observer import Subject

import builtins

if 'PyPDEVS' in builtins.__dict__['DEFAULT_DEVS_DIRNAME']:
	raise AssertionError("Blink plug-in is not compatible with the PyPDEVS simulation kernel!")

def InternalLog(model):
	txt = [	"\n\tINTERNAL TRANSITION: %s (%s)\n"%(model.__class__.__name__, model.myID),
			"\t  New State: %s\n"%(model.state),
			"\t  Output Port Configuration:\n"]

	for m in model.OPorts:
		if m in list(model.myOutput.keys()):
			txt.append("\t    %s: %s\n"%(m, model.myOutput[m]))
		else:
			txt.append("\t    %s: None\n" %(m))

	if model.myTimeAdvance == INFINITY:
		txt.append("\t  Next scheduled internal transition at INFINITY\n")
	else:
		txt.append("\t  Next scheduled internal transition at %f\n" %(model.myTimeAdvance))

	return ''.join(txt)

def ExternalLog(model):
	txt = [	"\n\tEXTERNAL TRANSITION: %s (%s)\n"%(model.__class__.__name__, model.myID),
			"\t  New State: %s\n"%(model.state),
			"\t  Input Port Configuration:\n"]

	txt.extend(["\t    %s: %s\n"%(m, model.peek(m)) for m in model.IPorts])

	if model.myTimeAdvance == INFINITY:
		txt.append("\t  Next scheduled internal transition at INFINITY\n")
	else:
		txt.append("\t  Next scheduled internal transition at %f\n" %(model.myTimeAdvance))

	return ''.join(txt)

def TimeAdvanceLog(model):
	txt = "\n\tTA CHECKING for %s (%s) : %f\n"%(model.__class__.__name__, model.myID, model.myTimeAdvance)
	return txt

def GetState(self):
	return self.__state

@pluginmanager.register("START_BLINK")
def start_blink(*args, **kwargs):

	global frame
	global sender
	global canvas

	parent = kwargs['parent']
	master = kwargs['master']

	### parent is simulationGUI and parent of it can be wx main app or DetachedFrame
	mainW = parent.GetParent()

	### find canvas depending on the parent of parent
	if isinstance(mainW, DetachedFrame):
		canvas = mainW.GetCanvas()
	else:
		nb = mainW.GetDiagramNotebook()
		actuel = nb.GetSelection()
		canvas = nb.GetPage(actuel)

	### define diagram
	diagram = canvas.GetDiagram()

	### define frame
	frame = BlinkFrame(parent, wx.NewIdRef(), _('Blink Logger'))
	frame.SetIcon(mainW.GetIcon())
	frame.SetTitle("%s Blink Logger"%os.path.basename(diagram.last_name_saved))
	frame.Show()

	### define sender
	sender = Subject()
	sender.canvas = canvas
	sender.__state = {}
	sender.GetState = MethodType(GetState, sender)

	### disable suspend and log button
	parent._btn3.Disable()
	parent._btn4.Disable()

@pluginmanager.register("SIM_BLINK")
def blink_manager(*args, **kwargs):
	""" Start blink.
	"""

	global frame
	global sender
	global canvas

	d = kwargs['model']
	msg = kwargs['msg']

	### if frame is deleted (occur for dynamic coupled model)
	if not isinstance(frame, wx.Frame):
		return

	### DEVSimPy block
	if hasattr(d, 'getBlockModel'):

		if isinstance(frame, wx.Frame):

			block = d.getBlockModel()

			#### add model d to observer list
			sender.attach(block)

			old_fill = block.fill

			### write external transition result
			if type(msg[0]) == type({}):
			#if msg == 0:
				color = ["#e90006"]
				f = ExternalLog(d)

			### write ta checking result
			elif msg[0] == 0:
			#elif msg == 2:
				color = ["#0c00ff"]
				f = TimeAdvanceLog(d)

			### write internal transition result
			elif msg[0] == 1:
			#elif msg == 1:
				color = ["#2E8B57"]
				f = InternalLog(d)

			else:
				color = old_fill

			state = sender.GetState()

			### blink frame is always active
			if frame and frame.IsShown():
				dastyle = wx.TextAttr()
				dastyle.SetTextColour(color[0])
				frame.txt.SetDefaultStyle(dastyle)

				wx.CallAfter(frame.txt.write,(f))
				#frame.txt.write(f)

				state['fill'] = color
				sender.notify()

				try:
				### step engine
					frame.flag = False
					while not frame.flag:
						pass
				except:
					pass
					
			### blink frame has been closed
			else:
				### assign the default color
				color = CodeBlock.FILL if isinstance(block, CodeBlock) else ContainerBlock.FILL
				state['fill'] = color
				sender.notify()
				
			### add model d to observer list
			sender.detach(block)

		else:
			wx.CallAfter(frame.txt.write,(_("Canvas is not found\n")))
	else:
		wx.CallAfter(frame.txt.write,(_("No blink for %s dynamic model (%s)!\n")%(str(d), d.myID)))

def Config(parent):
	""" Plug-in settings frame.
	"""
	dlg = wx.MessageDialog(parent, _('No settings available for this plug-in\n'), _('Blink configuration'), wx.OK | wx.ICON_EXCLAMATION)
	dlg.ShowModal()

class BlinkFrame(wx.Frame):
	"""
	"""
	def __init__(self, *args, **kwds):
		""" Constructor.
		"""
		super(BlinkFrame, self).__init__(*args, **kwds)

		### just for the start of the frame
		self.flag = True

		self.OnInit()

	def OnInit(self):

		panel = wx.Panel(self)
		
		self.button_clear = wx.Button(panel, wx.ID_CLEAR)
		self.button_step = wx.Button(panel, wx.ID_FORWARD)
		self.button_find = wx.Button(panel, wx.ID_FIND)
		self.button_selectall = wx.Button(panel, wx.ID_SELECTALL)
		self.txt = wx.TextCtrl(panel, style = wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2)

		### to close the frame when this attribute don't change
		self.lenght = self.txt.GetNumberOfLines()

		MoveFromParent(self, interval=10, direction='right')

		self.__set_properties()
		sizer = self.__do_layout()

		panel.SetSizerAndFit(sizer)

		### just for window
		self.SetClientSize(panel.GetBestSize())

		self.Bind(wx.EVT_BUTTON, self.OnStep, id=self.button_step.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnClear, id=self.button_clear.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnSelectAll, id=self.button_selectall.GetId())
		self.Bind(wx.EVT_BUTTON, self.OnFindReplace, id=self.button_find.GetId())
		self.Bind(wx.EVT_CLOSE, self.OnClose)

	def __set_properties(self):
		self.txt.SetMinSize((390, 300))
		txt1 = _("Press this button in order to go step by step in the simulation.")
		txt2 = ("Press this button in order to clean the output of the simulation.")
		txt3 = _("Press this button in order to launch the search window.")

		if wx.VERSION_STRING < '4.0':
			self.button_step.SetToolTipString(txt1)
			self.button_clear.SetToolTipString(txt2)
			self.button_find.SetToolTipString(txt3)
		else:
			self.button_step.SetToolTip(txt1)
			self.button_clear.SetToolTip(txt2)
			self.button_find.SetToolTip(txt3)

		self.button_step.SetDefault()

	def __do_layout(self):

		vbox = wx.BoxSizer(wx.VERTICAL)
		hbox = wx.BoxSizer(wx.HORIZONTAL)

		vbox.Add(self.txt, 1, wx.EXPAND)
		vbox.Add((-1,5))
		hbox.Add(self.button_selectall, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ADJUST_MINSIZE, 5)
		hbox.Add(self.button_find, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ADJUST_MINSIZE, 5)
		hbox.Add(self.button_clear, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ADJUST_MINSIZE, 5)
		vbox.Add(hbox, 0, wx.EXPAND)
		vbox.Add((-1,5))
		vbox.Add(self.button_step, 0, wx.ALIGN_RIGHT, 5)

		return vbox

	def OnStep(self, evt):
		"""
		"""
		nb = self.txt.GetNumberOfLines()
		
		### si plus de sortie text dans le Logger, alors on ferme la fentre et on stop la simulation
		if nb != self.lenght:
			self.lenght = nb
		else:
			parent = self.GetParent()
			parent.OnStop(evt)
			self.Close()
		
		self.flag = True
		self.button_clear.Enable(True)

	###
	def OnClear(self, evt):
		""" Clear selection or all text
		"""

		s = self.txt.GetSelection()
		### if no text selected, we select all
		if s[0] == s[1]:
			s = self.txt.SelectAll()

		s = self.txt.GetSelection()

		self.txt.Remove(s[0], s[1])

	###
	def OnSelectAll(self, evt):
		""" Select all text
		"""
		self.txt.SelectAll()

	###
	def OnFindReplace(self, evt):
		""" Call find and replace dialogue
		"""
		FindReplace(self, wx.NewIdRef(), _('Find/Replace'))

	def OnClose(self, evt):
		"""
		"""
		self.flag = True
		#self.Destroy()
		evt.Skip()