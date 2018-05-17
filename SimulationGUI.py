# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# SimulationGUI.py ---
#                     --------------------------------
#                        Copyright (c) 2010
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 16/11/13
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

import wx
import os
import sys
import copy
import threading

# to send event
if wx.VERSION_STRING < '2.9':
	from wx.lib.pubsub import Publisher as pub
else:
	#from wx.lib.pubsub import setuparg1
	from wx.lib.pubsub import pub

from tempfile import gettempdir

import __builtin__
import traceback
import re

### just for individual test
if __name__ == '__main__':
	__builtin__.__dict__['GUI_FLAG'] = True
	__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = "PyDEVS"
	__builtin__.__dict__['DEVS_DIR_PATH_DICT'] = {\
	'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),\
	'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')}

from Utilities import IsAllDigits, playSound
from pluginmanager import trigger_event, is_enable
from Patterns.Strategy import *
from Decorators import BuzyCursorNotification, hotshotit

import Container

_ = wx.GetTranslation

import time

def timer():
	last = time.time()
	delta = 0
	time.clock()
	while True:
	    now = time.time()
	    delta += now - last
	    yield delta
	    last = now
        
###
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

		if (len(text) == 0) or (not IsAllDigits(text)) or (float(text) <=0.0) :
			wx.MessageBox(_("The field must contain some positive numbers!"),_("Error Manager"))
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

class CollapsiblePanel(wx.Panel):
	def __init__(self, parent, simdia):

		wx.Panel.__init__(self, parent, -1)

		self.parent = parent
		### frame or panel !!!
		self.simdia = simdia

		self.org_w,self.org_h = self.simdia.GetSize()

		self.label1 = _("More settings...")
		self.label2 = _("Extra options")

		self.cp = wx.CollapsiblePane(self, label=self.label1,
											style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)

		self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, self.cp)
		self.MakePaneContent(self.cp.GetPane())

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.cp, 0, wx.EXPAND)
		self.SetSizer(sizer)

	def OnPaneChanged(self, evt=None):

		# redo the layout
		self.Layout()

		### new height to apply
		new_h = self.simdia.GetSize()[-1] #self.cp.GetSize()[-1]

		# and also change the labels
		if self.cp.IsExpanded():
			### change the collapsible label
			self.cp.SetLabel(self.label2)
			### adapt the window size
			self.simdia.SetSizeWH(-1, self.org_h+new_h)
			### Max limit
			self.simdia.SetMaxSize(wx.Size(self.simdia.GetSize()[0], self.org_h+new_h))
		else:
			### change the collapsible label
			self.cp.SetLabel(self.label1)
			### adapt the window size
			self.simdia.SetSizeWH(-1, self.org_h)

	def MakePaneContent(self, pane):
		'''Just make a few controls to put on the collapsible pane'''

		text2 = wx.StaticText(pane, wx.ID_ANY, _("%s algorithm:")%DEFAULT_DEVS_DIRNAME)

		### list of possible strategy depending on the PyDEVS version
		if DEFAULT_DEVS_DIRNAME == 'PyDEVS':
			c = PYDEVS_SIM_STRATEGY_DICT.keys()
		else:
			c = PYPDEVS_SIM_STRATEGY_DICT.keys()

		### choice of strategy
		ch1 = wx.Choice(pane, wx.ID_ANY, choices=c)

		text3 = wx.StaticText(pane, wx.ID_ANY, _("Profiling"))
		cb1 = wx.CheckBox(pane, wx.ID_ANY, name='check_prof')
		text4 = wx.StaticText(pane, wx.ID_ANY, _("No time limit"))
		self.cb2 = wx.CheckBox(pane, wx.ID_ANY, name='check_ntl')
		text5 = wx.StaticText(pane, wx.ID_ANY, _("Verbose"))
		self.cb3 = wx.CheckBox(pane, wx.ID_ANY, name='verbose')
		text6 = wx.StaticText(pane, wx.ID_ANY, _("Dynamic Structure"))
		cb4 = wx.CheckBox(pane, wx.ID_ANY, name='dyn_struct')
		
		text7 = wx.StaticText(pane, wx.ID_ANY, _("Real time"))
		cb5 = wx.CheckBox(pane, wx.ID_ANY, name='real_time')
		
		if DEFAULT_DEVS_DIRNAME == 'PyDEVS':
			if not 'hotshot' in sys.modules.keys():
				text3.Enable(False)
				cb1.Enable(False)
				self.parent.prof = False

			self.cb2.SetValue(__builtin__.__dict__['NTL'])
			self.cb3.Enable(False)
			cb4.Enable(False)
			cb5.Enable(False)
			
		else:
			cb1.Enable(False)
			self.cb2.SetValue(__builtin__.__dict__['NTL'])
			self.cb3.SetValue(__builtin__.__dict__['VERBOSE'])
			cb4.SetValue(__builtin__.__dict__['DYNAMIC_STRUCTURE'])
			cb5.SetValue(__builtin__.__dict__['REAL_TIME'])

		### default strategy
		if DEFAULT_DEVS_DIRNAME == 'PyDEVS':
			ch1.SetSelection(PYDEVS_SIM_STRATEGY_DICT.keys().index(DEFAULT_SIM_STRATEGY))
  		else:
			ch1.SetSelection(PYPDEVS_SIM_STRATEGY_DICT.keys().index(DEFAULT_SIM_STRATEGY))

		ch1.SetToolTipString(_("Select the simulator strategy."))
		cb1.SetToolTipString(_("For simulation profiling using hotshot"))
		self.cb2.SetToolTipString(_("No time limit for the simulation. Simulation is over when childs are no active."))

		grid3 = wx.GridSizer(6, 2, 1, 1)
		grid3.Add(text2, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(ch1, 1, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		grid3.Add(text3, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(cb1, 1, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(text4, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(self.cb2, 1, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(text5, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(self.cb3, 1, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(text6, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(cb4, 1, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(text7, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(cb5, 1, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 19)
		
		pane.SetSizer(grid3)

		self.Bind(wx.EVT_CHOICE, self.OnChoice, ch1)
		self.Bind(wx.EVT_CHECKBOX, self.OnProfiling, cb1)
		self.Bind(wx.EVT_CHECKBOX, self.OnNTL, self.cb2)
		self.Bind(wx.EVT_CHECKBOX, self.OnVerbose, self.cb3)
		self.Bind(wx.EVT_CHECKBOX, self.OnDynamicStructure, cb4)
		self.Bind(wx.EVT_CHECKBOX, self.OnRealTime, cb5)
		
	###
	def OnChoice(self, event):
		""" strategy choice has been invoked
		"""
		selected_string = event.GetString()
		self.simdia.selected_strategy = selected_string

		### update of ntl checkbox depending on the choosing strategy
		self.cb2.Enable(not (self.simdia.selected_strategy == 'original' and  DEFAULT_DEVS_DIRNAME == 'PyDEVS'))

		__builtin__.__dict__['DEFAULT_SIM_STRATEGY'] = self.simdia.selected_strategy

	def OnNTL(self, event):
		cb2 = event.GetEventObject()

		self.simdia.ntl = cb2.GetValue()
		self.simdia._text1.Enable(not self.simdia.ntl)
		self.simdia._value.Enable(not self.simdia.ntl)
		__builtin__.__dict__['NTL'] = self.simdia.ntl

	def OnProfiling(self, event):
		cb1 = event.GetEventObject()
		self.simdia.prof = cb1.GetValue()

	def OnVerbose(self, event):
		cb3 = event.GetEventObject()
		self.simdia.verbose = cb3.GetValue()
		__builtin__.__dict__['VERBOSE'] = self.simdia.verbose
		
	def OnDynamicStructure(self, event):
		cb4 = event.GetEventObject()
		self.simdia.dynamic_structure_flag = cb4.GetValue()
		__builtin__.__dict__['DYNAMIC_STRUCTURE'] = self.simdia.dynamic_structure_flag

	def OnRealTime(self, event):
		cb5 = event.GetEventObject()
		self.simdia.real_time_flag = cb5.GetValue()
		__builtin__.__dict__['REAL_TIME'] = self.simdia.real_time_flag
		
#-----------------------------------------------------------------
class Base(object):
	"""Base class for Simulation Dialog
		Frame or Panel with progress bar
	"""

	def __init__(self, parent, id, title, master):
		""" Constructor
		"""

#		if isinstance(parent, wx.Panel):
#			wx.Panel.__init__(self, parent, id)
#			self.SetBackgroundColour(wx.NullColour)
#			self.panel = self
#
#			### panel inherit of the left splitter size
#			self.panel.SetSize(parent.GetParent().GetSize())
#
#			# status bar of main application
#			self.statusbar = parent.GetTopLevelParent().statusbar
#		else:
#			wx.Frame.__init__(self, parent, id, title, style= wx.DEFAULT_FRAME_STYLE)
#
#			### adapt size of frame depending on the plate-form
#			if  '__WXMSW__' in wx.PlatformInfo:
#				self.SetSize((320,280))
#			else:
#				self.SetSize((280,160))
#
#			# disable the roll out of the frame
#			self.SetMinSize(self.GetSize())
#
#			self.panel = wx.Panel(self, -1)
#
#			wx.CallAfter(self.CreateBar)
#
#			self.__set_properties()

		# local copy
		self.parent = parent
		self.master = master
		self.title = title

		### current master for multi-simulation without simulationDialog reloading (show OnOk)
		self.current_master = None

		# simulator strategy
		self.selected_strategy = DEFAULT_SIM_STRATEGY

		### dynamic structure only for local PyPDEVS simulation
		self.dynamic_structure_flag = __builtin__.__dict__['DYNAMIC_STRUCTURE']

		### PyPDEVS threaded real time simulation
		self.real_time_flag = __builtin__.__dict__['REAL_TIME']
		
		### profiling simulation with hotshot
		self.prof = False

		### No time limit simulation (defined in the builtin dictionary from .devsimpy file)
		self.ntl = __builtin__.__dict__['NTL']

		self.verbose = __builtin__.__dict__['VERBOSE']

		# definition of the thread, the timer and the counter for the simulation progress
		self.thread = None
		self.timer = wx.Timer(self, wx.NewId())
		self.count = 10.0
		self.stdioWin = None

		self.__widgets()
		self.__do_layout()
		self.__set_events()

		### create a pubsub receiver (simple way to communicate with thread)
		pub.subscribe(self.ErrorManager, "error")

	def CreateBar(self):
		self.statusbar = self.CreateStatusBar(2)

	def __widgets(self):

		self._text1 = wx.StaticText(self.panel, wx.ID_ANY, _('Final time:'))
		self._value = wx.TextCtrl(self.panel, wx.ID_ANY, str(float(self.master.FINAL_TIME)), validator=TextObjectValidator())
		self._btn1 = wx.Button(self.panel, wx.NewId(), _('Run'))
		self._btn2 = wx.Button(self.panel, wx.NewId(), _('Stop'))
		self._btn3 = wx.Button(self.panel, wx.NewId(), _('Suspend'))
		self._btn4 = wx.Button(self.panel, wx.NewId(), _('Log'))
		self._gauge = wx.Gauge(self.panel, wx.ID_ANY, 100, size=(-1, 25), style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
		self._cp = CollapsiblePanel(self.panel, self)

		self._text1.Enable(not self.ntl)
		self._value.Enable(not self.ntl)

		self._btn1.SetToolTipString(_("Begin simulation process."))
		self._btn2.SetToolTipString(_("Stop the simulation process."))
		self._btn3.SetToolTipString(_("Suspend the simulation process."))
		self._btn4.SetToolTipString(_("Launch the log window (often depends on some plug-ins (verbose, activity, ...))."))

	def __do_layout(self):

		#vbox_top = wx.BoxSizer(wx.VERTICAL)
		vbox_body = wx.BoxSizer(wx.VERTICAL)

		#panel 1
		grid1 = wx.GridSizer(1, 2, 0, 0)
		grid1.Add(self._text1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
		grid1.Add(self._value, 1, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)

		# panel2
		grid2 = wx.GridSizer(3, 2, 2, 2)
		grid2.Add(self._btn1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
		grid2.Add(self._btn3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
		grid2.Add(self._btn2, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
		grid2.Add(self._btn4, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)

		# panel4
		#hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		#hbox1.Add(self._gauge, 1, wx.EXPAND, 9)

		## panel5
		#hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		#hbox2.Add(self._cp, 1, wx.EXPAND, 9)

		vbox_body.Add(grid1, 0, wx.EXPAND, 9)
		vbox_body.Add(grid2, 0, wx.EXPAND, 9)
		vbox_body.Add(self._gauge, 0, wx.EXPAND, 9)
		vbox_body.Add(self._cp, 0, wx.EXPAND, 9)

		# fin panel
		#vbox_top.Add(vbox_body, 0, wx.EXPAND|wx.ALL, 9)
		self.panel.SetSizer(vbox_body)

#		vbox_body.Fit(self)

		self._text1.SetFocus()
		self._btn1.SetDefault()
		self._btn2.Disable()
		self._btn3.Disable()

	###
	def __set_events(self):

		### binding event
		self.Bind(wx.EVT_BUTTON, self.OnOk, self._btn1)
		self.Bind(wx.EVT_BUTTON, self.OnStop, self._btn2)
		self.Bind(wx.EVT_BUTTON, self.OnSuspend, self._btn3)
		self.Bind(wx.EVT_BUTTON, self.OnViewLog, self._btn4)
		self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
		self.Bind(wx.EVT_TEXT,self.OnText, self._value)
		self.Bind(wx.EVT_CLOSE, self.OnQuit)

	###
	def ChangeButtonLabel(self, btn, new_label):
		""" Change the label of the Log button depending on the active plug-in
		"""

		### if activity plug-in is enabled
		if is_enable('start_activity_tracking'):
			self._btn4.SetLabel("Activity")

	###
	def OnText(self, event):
		self._gauge.SetValue(0)

	###
	@BuzyCursorNotification
	def OnViewLog(self, event):
		"""	When View button is clicked
		"""
		# The simulation verbose event occurs
		trigger_event('START_SIM_VERBOSE', parent=self)

		# The simulation verbose event occurs
		trigger_event('VIEW_ACTIVITY_REPORT', parent=self, master=self.current_master)

	###
	def OnOk(self, event):
		""" When Run button is clicked
		"""

		assert(self.master is not None)

		if self._value.GetValidator().Validate(self._value) or self.ntl:

			### pour prendre en compte les simulations multiples sans relancer un SimulationDialog
			### si le thread n'est pas lancé (pas pendant un suspend)
			if self.thread is not None and not self.thread.thread_suspend:
				diagram = self.master.getBlockModel()
				diagram.Clean()
				self.current_master = Container.Diagram.makeDEVSInstance(diagram)
			else:
				self.current_master = self.master

			if isinstance(self.parent, wx.Panel):
				# redirection du stdout ici dans le cas du Panel (sinon dans OnSimulation)
				mainW = self.parent.GetTopLevelParent()
				sys.stdout = mainW.stdioWin

			### test si le modele et bien charge
			if (self.current_master == None) or (self.current_master.componentSet == []):
				return self.MsgBoxEmptyModel()

			### dont erase the gauge if ntl
			if not self.ntl:
				# stockage du temps de simulation dans le master
				self.current_master.FINAL_TIME = float(self._value.GetValue())
				self._gauge.SetValue(0)
				### if _gauge is wx.Slider
				#self._gauge.SetMax(self.current_master.FINAL_TIME)

			self.statusbar.SetBackgroundColour('')
			self.statusbar.SetStatusText("", 1)
			if self.statusbar.GetFieldsCount() > 2:
				self.statusbar.SetStatusText("", 2)

			if (self.thread is None) or (not self.timer.IsRunning()):

				trigger_event("START_BLINK", parent=self, master=self.current_master)
				trigger_event("START_TEST", parent=self, master=self.current_master)

				### The START_ACTIVITY_TRACKING event occurs
				trigger_event("START_ACTIVITY_TRACKING", parent=self, master=self.current_master)

				### The START_ACTIVITY_TRACKING event occurs
				trigger_event("START_STATE_TRAJECTORY", parent=self, master=self.current_master)

				### The START_CONCURRENT_SIMULATION event occurs
				trigger_event("START_CONCURRENT_SIMULATION", parent=self, master=self.current_master)

				### future call is required because the simulator is flattened during the execution of the strategy 3
				wx.FutureCall(1, trigger_event, 'START_DIAGRAM', parent=self, master=self.current_master)

				### clear all log file
				for fn in filter(lambda f: f.endswith('.devsimpy.log'), os.listdir(gettempdir())):
					os.remove(os.path.join(gettempdir(),fn))

				self.thread = simulator_factory(self.current_master, self.selected_strategy, self.prof, self.ntl, self.verbose, self.dynamic_structure_flag, self.real_time_flag)
				self.thread.setName(self.title)

				### si le modele n'a pas de couplage, ou si pas de generateur: alors pas besoin de simuler
				if self.thread.end_flag:
					self.OnTimer(event)
				else:
					self.timer.Start(100)

				### timer for real time
				if self.real_time_flag: 
					self.t = timer()
		
			else:
				#print self.thread.getAlgorithm().trace
				### for back simulation
				#self.thread.s = shelve.open(self.thread.f.name+'.db',flag='r')
				#self.thread.model = self.thread.s['s'][str(float(self._gauge.GetValue()))]

				### restart the hiding gauge
				if self.ntl:
					self._gauge.Show()

				### restart thread
				self.thread.resume_thread()

			self.Interact(False)

			if self.count >= 100:
				return

			### interaction with the model is not possible
			#self.parent.Enable(False)

	def Interact(self, access = True):
		""" Enabling and disabling options (buttons, checkbox, ...)
		"""

		self._btn1.Enable(access)
		self._btn2.Enable(not access)
		self._btn3.Enable(not access)
		self._value.Enable(not self.ntl)
		self._cp.Enable(access)

	###
	def OnStop(self, event):
		""" When Stop button is clicked
		"""

		self.Interact()
		if self.thread : self.thread.terminate()
		self.timer.Stop()
		wx.Bell()

		self._gauge.SetValue(0)
		self.statusbar.SetBackgroundColour('')
		self.statusbar.SetStatusText(_('Interrupted'), 0)
		self.statusbar.SetStatusText("", 1)
		if self.statusbar.GetFieldsCount() > 2:
			self.statusbar.SetStatusText("", 2)

	###
	def OnSuspend(self, event):
		""" When suspend button is clicked
		"""

		self.Interact()
		self.thread.suspend()

		if self.ntl:
			self._gauge.Hide()

		if self.count == 0 or self.count >= 100 or not self.timer.IsRunning():
			return

		self.statusbar.SetStatusText(_('Suspended'),0)

		# way to interact with the model
		#self.parent.Enable(True)
		wx.Bell()

	###
	def OnTimer(self, event):
		""" Give the pourcentage of simulation progress
		"""

		### if no time limit, gauge pulse
		if self.ntl:
			self._gauge.Pulse()
		else:
			if not isinstance(self.thread.model.timeLast, tuple):
				timeLast = self.thread.model.timeLast
			else:
				timeLast = self.thread.model.timeLast[0]

			self.count = (timeLast/self.thread.model.FINAL_TIME)*100

			self._gauge.SetValue(self.count)

		### if simulation is over
		if self.thread.end_flag:

			### update the status of buttons
			self._btn1.Enable(True)
			self._btn2.Disable()
			self._btn3.Disable()
			self._value.Enable(not self.ntl)
			self._cp.Enable()

			### check if gauge is full (can appear if timer is too slow)
			if self.count != 100:
				self.count = 100
				self._gauge.SetValue(self.count)

			### update the status bar
			self.statusbar.SetBackgroundColour('')
			self.statusbar.SetStatusText(_("Completed!"), 0)
			self.statusbar.SetStatusText(self.GetClock(), 1)

			### is no time limit add some informations in status bar
			if not self.ntl:
				if self.statusbar.GetFieldsCount() > 2:
					self.statusbar.SetStatusText(str(100)+"%", 2)

			### stop the timer
			self.timer.Stop()

		### if the simulation is suspended
		elif not self.thread.thread_suspend:

			### udpate the status bar
			self.statusbar.SetBackgroundColour('GREY')
			self.statusbar.SetStatusText(_("Processing..."), 0)
			self.statusbar.SetStatusText(self.GetClock(), 1)
			#self.statusbar.SetStatusText("%0.4f s"%(self.thread.cpu_time), 1)

			### is no time limit, add some information in status bar
			if not self.ntl:
				if self.statusbar.GetFieldsCount() > 2:
					self.statusbar.SetStatusText(str(self.count)[:4]+"%", 2)

			#wx.Yield()
			wx.YieldIfNeeded()

	def GetClock(self):
		if self.real_time_flag:	
			return str(self.t.next())
		else:
			### clock formating
			ms = self.thread.cpu_time%1
			m, s = divmod(self.thread.cpu_time, 60)
			h, m = divmod(m, 60)
			return "%d:%02d:%02d:%03d" % (h, m, s, ms*1000)

	###
	def MsgBoxEmptyModel(self):
		""" Pop-up alert for empty model
		"""
		dial = wx.MessageDialog(self,
							_('You want to simulate an empty master model!'),
							_('Simulation Manager'),
							wx.OK|wx.ICON_EXCLAMATION)

		if (dial.ShowModal() == wx.ID_OK) and (isinstance(self.parent, wx.Frame)):
			self.DestroyWin()
		else:
			return

	def SetFields(self):
		"""
		"""
		if wx.VERSION_STRING < '4.0':
			self.statusbar.SetFields([""]*self.statusbar.GetFieldsCount())
		else:
			for i in range(self.statusbar.GetFieldsCount()):
				self.statusbar.SetStatusText("",i)

	def DestroyWin(self):
		""" To destroy the simulation frame
		"""

		### clean status bar
		self.statusbar.SetBackgroundColour('')
		self.SetFields()

		### try to hidden stdioWin
		try:
			self.parent.stdioWin.frame.Show(False)
		except:
			pass

		try:
		## left panel enabled
			nb1 = self.parent.mainW.GetControlNotebook()
			nb1.Enable()

			## menu enabled
			self.parent.tb.Enable()
			for i in xrange(self.parent.menuBar.GetMenuCount()):
				self.parent.menuBar.EnableTop(i,True)

			### other tab diagram enabled
			nb2 = self.parent.GetDiagramNotebook()
			for p in xrange(nb2.GetPageCount()):
				## pour tout les tab non selectionner
				if p != nb2.GetSelection():
					nb2.GetPage(p).Enable()

		except Exception:
			#sys.stdout.write(_("Empty mode over\n"))
			pass

		### destroy the frame
		self.Destroy()

	def OnQuit(self, event):
		""" When the simulation are stopping
		"""

		# if the simulation is running
		if self.timer.IsRunning():
			dial = wx.MessageDialog(self,
									_('Are you sure to stop simulation?'),
									_('Simulation Manager'),
									wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			self.thread.suspend()

			### if user wants to stop simulation process
			if dial.ShowModal() == wx.ID_YES:
				self.DestroyWin()
				self.thread.terminate()
			else:
				self.thread.resume_thread()

		else:
			self.DestroyWin()

	def ErrorManager(self, msg):
		""" An error is occurred.
		"""

		### try to find the file which have the error from traceback
		devs_error = False
		try:
			typ, val, tb = msg.date if wx.VERSION_STRING < '2.9' else msg
			trace = traceback.format_exception(typ, val, tb)

			mainW = wx.GetApp().GetTopWindow()
			### paths in traceback
			paths = filter(lambda a: a.split(',')[0].strip().startswith('File'), trace)
			### find if DOMAIN_PATH is in paths list (inversed because traceback begin by the end)
			for path in paths[::-1]:
				### find if one path in trace comes from Domain or exported path list
				for d in [DOMAIN_PATH]+mainW.GetExportPathsList():

					if d in path:
						devs_error = True
						break

		except Exception, info:
			print _("Error in ErrorManager: %s"%info)

		### if error come from devs python file
		if devs_error:

			try:
				### simulate event button for the code editor
				event = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, self._btn1.GetId())
			except:
				pass
			else:
				### Error dialog
				if not Container.MsgBoxError(event, self.parent, msg.date if wx.VERSION_STRING < '2.9' else msg):
				### if user dont want correct the error, we destroy the simulation windows
					self.DestroyWin()
				else:
				### if user want to correct error through an editor, we stop simulation process for trying again after the error is corrected.
					self.OnStop(event)
		else:
			raise msg

class SimulationDialogPanel(Base, wx.Panel):
	""" Simulation Dialog Panel 
	""" 
	def __init__(self, parent, id, title, master):
		""" Constructor
		"""
	
		assert(isinstance(parent, wx.Panel))
		
		wx.Panel.__init__(self, parent, id)
		self.SetBackgroundColour(wx.NullColour)
		self.panel = self

		### panel inherit of the left splitter size
		self.panel.SetSize(parent.GetParent().GetSize())

		# status bar of main application
		self.statusbar = parent.GetTopLevelParent().statusbar
		
		Base.__init__(self, parent, id, title, master)

class SimulationDialogFrame(Base, wx.Frame):
	""" SimulationDialog(parent, id, title, master)

		Frame or Panel with progress bar
	"""

	def __init__(self, parent, id, title, master):
		""" Constructor
		"""

		assert(isinstance(parent, wx.Frame))
		
		wx.Frame.__init__(self, parent, id, title, style= wx.DEFAULT_FRAME_STYLE)

		### adapt size of frame depending on the plate-form
		if  '__WXMSW__' in wx.PlatformInfo:
			self.SetSize((320,280))
		else:
			self.SetSize((280,160))

		# disable the roll out of the frame
		self.SetMinSize(self.GetSize())

		self.panel = wx.Panel(self, -1)

		wx.CallAfter(self.CreateBar)
		
		Base.__init__(self, parent, id, title, master)
		
		self.__set_properties()

	def __set_properties(self):
		icon = wx.EmptyIcon()
		icon.CopyFromBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, "simulation.png"), wx.BITMAP_TYPE_ANY))
		self.SetIcon(icon)

		self.Center()
		
def SimulationDialog(*args):
	parent = args[0]
	if isinstance(parent, wx.Panel):
		return SimulationDialogPanel(*args)
	else:
		return SimulationDialogFrame(*args)
	
def simulator_factory(model, strategy, prof, ntl, verbose, dynamic_structure_flag, real_time_flag):
	""" Preventing direct creation for Simulator
        disallow direct access to the classes
	"""

	### find the correct simulator module depending on the
	for pydevs_dir, filename in __builtin__.__dict__['DEVS_DIR_PATH_DICT'].items():
		if pydevs_dir == __builtin__.__dict__['DEFAULT_DEVS_DIRNAME']:
			from DEVSKernel.PyDEVS.simulator import Simulator as BaseSimulator

	class Simulator(BaseSimulator):
		"""
		"""
		###
		def __init__(self, model):
			"""Constructor.
			"""

			BaseSimulator.__init__(self, model)

			self.model = model
			self.__algorithm = SimStrategy1(self)

		def simulate(self, T = sys.maxint):
			return self.__algorithm.simulate(T)

		def getMaster(self):
			return self.model

		def setMaster(self, model):
			self.model = model

		def setAlgorithm(self, s):
			self.__algorithm = s

		def getAlgorithm(self):
			return self.__algorithm

	class SimulationThread(threading.Thread, Simulator):
		"""
			Thread for DEVS simulation task
		"""

		def __init__(self, model = None, strategy = '', prof = False, ntl = False, verbose=False, dynamic_structure_flag=False, real_time_flag=False):
			""" Constructor.
			"""
			threading.Thread.__init__(self)
			Simulator.__init__(self, model)

			### local copy
			self.strategy = strategy
			self.prof = prof
			self.ntl = ntl
			self.verbose = verbose
			self.dynamic_structure_flag = dynamic_structure_flag
			self.real_time_flag = real_time_flag

			self.end_flag = False
			self.thread_suspend = False
			self.sleep_time = 0.0
			self.thread_sleep = False
			self.cpu_time = -1

			self.start()

		@hotshotit
		def run(self):
			""" Run thread
			"""

			### define the simulation strategy
			args = {'simulator':self}
			### TODO: isinstance(self, PyDEVSSimulator)
			if DEFAULT_DEVS_DIRNAME == "PyDEVS":
				cls_str = eval(PYDEVS_SIM_STRATEGY_DICT[self.strategy])
			else:
				cls_str = eval(PYPDEVS_SIM_STRATEGY_DICT[self.strategy])

			self.setAlgorithm(apply(cls_str, (), args))

			while not self.end_flag:
				### traceback exception engine for .py file
				try:
					self.simulate(self.model.FINAL_TIME)
				except Exception, info:
					self.terminate(error=True, msg=sys.exc_info())

		def terminate(self, error = False, msg = None):
			""" Thread termination routine
				param error: False if thread is terminate without error
				param msg: message to submit
			"""

			if not self.end_flag:
				if error:

					###for traceback
					etype = msg[0]
					evalue = msg[1]
					etb = traceback.extract_tb(msg[2])
					sys.stderr.write('Error in routine: your routine here\n')
					sys.stderr.write('Error Type: ' + str(etype) + '\n')
					sys.stderr.write('Error Value: ' + str(evalue) + '\n')
					sys.stderr.write('Traceback: ' + str(etb) + '\n')

					### only for displayed application (-nogui)
					if wx.GetApp():
						if wx.VERSION_STRING < '2.9':
							wx.CallAfter(pub.sendMessage,"error", msg)
						else:
							wx.CallAfter(pub.sendMessage,"error", msg=msg)

						### error sound
						wx.CallAfter(playSound, SIMULATION_ERROR_SOUND_PATH)

				else:
					for m in filter(lambda a: hasattr(a, 'finish'), self.model.componentSet):
						### call finished method
						if __builtin__.__dict__['GUI_FLAG']:
							if wx.VERSION_STRING < '2.9':
								pub.sendMessage('%d.finished'%(id(m)))
							else:
								pub.sendMessage('%d.finished'%(id(m)), msg="")
						else:
							m.finish(None)

					### resionly for displayed application (-nogui)
					if wx.GetApp() : wx.CallAfter(playSound, SIMULATION_SUCCESS_SOUND_PATH)

			self.end_flag = True

		def set_sleep(self, sleeptime):
			self.thread_sleep = True
			self._sleeptime = sleeptime

		def suspend(self):

			#main_thread = threading.currentThread()
			#for t in threading.enumerate():
			#	t.thread_suspend = True

			self.thread_suspend = True

		def resume_thread(self):
			self.thread_suspend = False

	return SimulationThread(model, strategy, prof, ntl, verbose, dynamic_structure_flag, real_time_flag)

### ------------------------------------------------------------
class TestApp(wx.App):
	""" Testing application
	"""

	def OnInit(self):

		__builtin__.__dict__['PYDEVS_SIM_STRATEGY_DICT'] = {'original':'SimStrategy1', 'bag-based':'SimStrategy2', 'direct-coupling':'SimStrategy3'}
		__builtin__.__dict__['PYPDEVS_SIM_STRATEGY_DICT'] = {'classic':'SimStrategy4', 'distribued':'SimStrategy5', 'parallel':'SimStrategy6'}
		__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = 'PyPDEVS'
		__builtin__.__dict__['DEVS_DIR_PATH_DICT'] = {'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')}

		import gettext
		import DomainInterface.MasterModel

		__builtin__.__dict__['ICON_PATH_16_16']=os.path.join('icons','16x16')
		__builtin__.__dict__['DEFAULT_SIM_STRATEGY'] = 'original'
		__builtin__.__dict__['NTL'] = False
		__builtin__.__dict__['_'] = gettext.gettext


		self.frame = SimulationDialog(None, wx.ID_ANY, 'Simulator', DomainInterface.MasterModel.Master())
		self.frame.Show()
		return True

	def OnQuit(self, event):
		self.Close()

if __name__ == '__main__':

	app = TestApp(0)
	app.MainLoop()