# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# SimulationGUI.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 03/15/20
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

import builtins
import wx
import os
import sys
import traceback

# to send event
from pubsub import pub

from tempfile import gettempdir

### just for individual test
if __name__ == '__main__':
	builtins.__dict__['GUI_FLAG'] = True
	builtins.__dict__['HOME_PATH'] = os.path.abspath(os.path.dirname(sys.argv[0]))
	builtins.__dict__['DEFAULT_DEVS_DIRNAME'] = "PyDEVS"
	builtins.__dict__['DEVS_DIR_PATH_DICT'] = {\
	'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),\
	'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS', 'old')}

from Utilities import IsAllDigits, printOnStatusBar
from PluginManager import PluginManager #trigger_event, is_enable
from Patterns.Strategy import *
from Patterns.Factory import simulator_factory
from Decorators import BuzyCursorNotification

import Container

import gettext
_ = gettext.gettext

import time

def timer():
	last = time.time()
	delta = 0
	time.time()
	while True:
	    now = time.time()
	    delta += now - last
	    yield delta
	    last = now
        
if wx.VERSION_STRING >= '4.0':
	wx.PyValidator = wx.Validator

class MyBad(Exception):pass

###
class TextObjectValidator(wx.PyValidator):
	""" TextObjectValidator()
	"""

	def __init__(self, *args, **kwargs):
		super(TextObjectValidator, self).__init__(*args, **kwargs)

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

		wx.Panel.__init__(self, parent)

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
			self.simdia.SetSize(-1, self.org_h+new_h)
			### Max limit
			self.simdia.SetMaxSize(wx.Size(self.simdia.GetSize()[0], self.org_h+new_h))
		else:
			### change the collapsible label
			self.cp.SetLabel(self.label1)
			### adapt the window size
			self.simdia.SetSize(-1, self.org_h)

	def MakePaneContent(self, pane):
		'''Just make a few controls to put on the collapsible pane'''

		text2 = wx.StaticText(pane, wx.NewIdRef(), _("%s algorithm:")%DEFAULT_DEVS_DIRNAME)

		### list of possible strategy depending on the PyDEVS version
		#if DEFAULT_DEVS_DIRNAME == 'PyDEVS':
		c = list(eval("%s_SIM_STRATEGY_DICT.keys()"%DEFAULT_DEVS_DIRNAME.upper()))
		#else:
		#	c = list(PYPDEVS_SIM_STRATEGY_DICT.keys())

		### choice of strategy
		ch1 = wx.Choice(pane, wx.NewIdRef(), choices=c)

		text3 = wx.StaticText(pane, wx.NewIdRef(), _("Profiling"))
		cb1 = wx.CheckBox(pane, wx.NewIdRef(), name='check_prof')
		text4 = wx.StaticText(pane, wx.NewIdRef(), _("No time limit"))
		self.cb2 = wx.CheckBox(pane, wx.NewIdRef(), name='check_ntl')
		text5 = wx.StaticText(pane, wx.NewIdRef(), _("Verbose"))
		self.cb3 = wx.CheckBox(pane, wx.NewIdRef(), name='verbose')
		text6 = wx.StaticText(pane, wx.NewIdRef(), _("Dynamic Structure"))
		cb4 = wx.CheckBox(pane, wx.NewIdRef(), name='dyn_struct')
		
		text7 = wx.StaticText(pane, wx.NewIdRef(), _("Real time"))
		cb5 = wx.CheckBox(pane, wx.NewIdRef(), name='real_time')
		
		if DEFAULT_DEVS_DIRNAME == 'PyDEVS':
			self.cb2.SetValue(builtins.__dict__['NTL'])
			self.cb3.Enable(False)
			cb4.Enable(False)
			cb5.Enable(False)
			
		else:
			cb1.Enable(False)
			self.cb2.SetValue(builtins.__dict__['NTL'])
			self.cb3.SetValue(builtins.__dict__['VERBOSE'])
			cb4.SetValue(builtins.__dict__['DYNAMIC_STRUCTURE'])
			cb5.SetValue(builtins.__dict__['REAL_TIME'] and not builtins.__dict__['NTL'])

		### default strategy
		#if DEFAULT_DEVS_DIRNAME == 'PyDEVS':
		ch1.SetSelection(list(eval("%s_SIM_STRATEGY_DICT.keys()"%DEFAULT_DEVS_DIRNAME.upper())).index(DEFAULT_SIM_STRATEGY))
		#else:
		#	ch1.SetSelection(list(PYPDEVS_SIM_STRATEGY_DICT.keys()).index(DEFAULT_SIM_STRATEGY))

		if wx.VERSION_STRING >= '4.0':
			ch1.SetToolTipString=ch1.SetToolTip
			cb1.SetToolTipString=cb1.SetToolTip
			self.cb2.SetToolTipString=self.cb2.SetToolTip

		ch1.SetToolTipString(_("Select the simulator strategy."))
		cb1.SetToolTipString(_("For simulation profiling using hotshot"))
		self.cb2.SetToolTipString(_("No time limit for the simulation. Simulation is over when childs are no active."))
		
		grid3 = wx.GridSizer(6, 2, 1, 1)
		grid3.Add(text2, 0, wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(ch1, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		grid3.Add(text3, 0, wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(cb1, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(text4, 0, wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(self.cb2, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(text5, 0, wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(self.cb3, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(text6, 0, wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(cb4, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(text7, 0, wx.ALIGN_CENTER_VERTICAL, 19)
		grid3.Add(cb5, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 19)
		
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

		builtins.__dict__['DEFAULT_SIM_STRATEGY'] = self.simdia.selected_strategy

	def OnNTL(self, event):
		cb2 = event.GetEventObject()

		self.simdia.ntl = cb2.GetValue()
		self.simdia._text1.Enable(not self.simdia.ntl)
		self.simdia._value.Enable(not self.simdia.ntl)
		builtins.__dict__['NTL'] = self.simdia.ntl

	def OnProfiling(self, event):
		cb1 = event.GetEventObject()
		self.simdia.prof = cb1.GetValue()

	def OnVerbose(self, event):
		cb3 = event.GetEventObject()
		self.simdia.verbose = cb3.GetValue()
		builtins.__dict__['VERBOSE'] = self.simdia.verbose
		
	def OnDynamicStructure(self, event):
		cb4 = event.GetEventObject()
		self.simdia.dynamic_structure_flag = cb4.GetValue()
		builtins.__dict__['DYNAMIC_STRUCTURE'] = self.simdia.dynamic_structure_flag

	def OnRealTime(self, event):
		cb5 = event.GetEventObject()
		self.simdia.real_time_flag = cb5.GetValue()
		builtins.__dict__['REAL_TIME'] = self.simdia.real_time_flag
		
#-----------------------------------------------------------------
class Base(object):
	"""Base class for Simulation Dialog
		Frame or Panel with progress bar
	"""

	def __init__(self, parent, id, title):
		""" Constructor
		"""

		# local copy
		self.parent = parent
		#self.master = master
		self.title = title

		### current master for multi-simulation without simulationDialog reloading (show OnOk)
		self.current_master = None

		# simulator strategy
		self.selected_strategy = DEFAULT_SIM_STRATEGY

		### dynamic structure only for local PyPDEVS simulation
		self.dynamic_structure_flag = builtins.__dict__['DYNAMIC_STRUCTURE']

		### PyPDEVS threaded real time simulation
		self.real_time_flag = builtins.__dict__['REAL_TIME']
		
		### profiling simulation
		self.prof = False

		### No time limit simulation (defined in the builtin dictionary from .devsimpy file)
		self.ntl = builtins.__dict__['NTL']

		self.verbose = builtins.__dict__['VERBOSE']

		# definition of the thread, the timer and the counter for the simulation progress
		self.thread = None
		self.timer = wx.Timer(self, wx.NewIdRef())
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

		self._text1 = wx.StaticText(self.panel, wx.NewIdRef(), _('Final time:'))
		self._value = wx.TextCtrl(self.panel, wx.NewIdRef(), validator=TextObjectValidator())
		self._btn1 = wx.Button(self.panel, wx.NewIdRef(), _('Run'))
		self._btn2 = wx.Button(self.panel, wx.NewIdRef(), _('Stop'))
		self._btn3 = wx.Button(self.panel, wx.NewIdRef(), _('Suspend'))
		self._btn4 = wx.Button(self.panel, wx.NewIdRef(), _('Log'))
		self._gauge = wx.Gauge(self.panel, wx.NewIdRef(), 100, size=(-1, 25), style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
		self._cp = CollapsiblePanel(self.panel, self)

		self.SetNTL(self.ntl)

		if wx.VERSION_STRING >= '4.0':
			self._btn1.SetToolTipString = self._btn1.SetToolTip
			self._btn2.SetToolTipString = self._btn2.SetToolTip
			self._btn3.SetToolTipString = self._btn3.SetToolTip
			self._btn4.SetToolTipString = self._btn4.SetToolTip

		self._btn1.SetToolTipString(_("Begin simulation process."))
		self._btn2.SetToolTipString(_("Stop the simulation process."))
		self._btn3.SetToolTipString(_("Suspend the simulation process."))
		self._btn4.SetToolTipString(_("Launch the log window (often depends on some plug-ins (verbose, activity, ...))."))

	def SetNTL(self, ntl):
		self.ntl = ntl
		self._text1.Enable(not ntl)
		self._value.Enable(not ntl)
		self._cp.cb2.SetValue(ntl)

	def SetTime(self, time):
		self._value.SetValue(time)

	def SetMaster(self, master):
		self.master = master
		self._value.SetValue(str(float(self.master.FINAL_TIME)))

	def GetMaster(self):
		self.master

	def __do_layout(self):

		vbox_body = wx.BoxSizer(wx.VERTICAL)

		#panel 1
		grid1 = wx.GridSizer(1, 2, 0, 0)
		grid1.Add(self._text1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
		grid1.Add(self._value, 1, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)

		# panel2
		grid2 = wx.GridSizer(3, 2, 2, 2)
		grid2.Add(self._btn1, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		grid2.Add(self._btn3, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		grid2.Add(self._btn2, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		grid2.Add(self._btn4, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		vbox_body.Add(grid1, 0, wx.EXPAND|wx.TOP, 9)
		vbox_body.Add((-1, 10))
		vbox_body.Add(grid2, 0, wx.EXPAND, 9)
		vbox_body.Add(self._gauge, 0, wx.EXPAND, 9)
		vbox_body.Add(self._cp, 0, wx.EXPAND, 9)

		# fin panel
		self.panel.SetSizer(vbox_body)

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
		if PluginManager.is_enable('start_activity_tracking'):
			self._btn4.SetLabel("Activity")

	###
	def OnText(self, event):
		"""
		"""
		self._gauge.SetValue(0)

	###
	@BuzyCursorNotification
	def OnViewLog(self, event):
		"""	When View button is clicked
		"""
		# The simulation verbose event occurs
		PluginManager.trigger_event('START_SIM_VERBOSE', parent=self)

		# The activity tracking event occurs
		PluginManager.trigger_event('VIEW_ACTIVITY_REPORT', parent=self, master=self.current_master)

	###
	def OnOk(self, event):
		""" When Run button is clicked.
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
				# stdout redirect only for the Panel mode (if not in OnSimulation)
				mainW = self.parent.GetTopLevelParent()
				sys.stdout = mainW.stdioWin

			### check is model is well loaded
			if (self.current_master is None) or (len(self.current_master.getComponentSet()) == 0):
				return self.MsgBoxEmptyModel()
			
			### dont erase the gauge if ntl
			if not self.ntl:
				# simulation time stored in the master model
				self.current_master.FINAL_TIME = float(self._value.GetValue())
				self._gauge.SetValue(0)
				### if _gauge is wx.Slider
				#self._gauge.SetMax(self.current_master.FINAL_TIME)

			self.statusbar.SetBackgroundColour('')
			printOnStatusBar(self.statusbar, {1:""})
			if self.statusbar.GetFieldsCount() > 2:
				printOnStatusBar(self.statusbar, {2:""})

			if (self.thread is None) or (not self.timer.IsRunning()):

				PluginManager.trigger_event("START_BLINK", parent=self, master=self.current_master)
				PluginManager.trigger_event("START_TEST", parent=self, master=self.current_master)

				### The START_ACTIVITY_TRACKING event occurs
				PluginManager.trigger_event("START_ACTIVITY_TRACKING", parent=self, master=self.current_master)

				### The START_ACTIVITY_TRACKING event occurs
				PluginManager.trigger_event("START_STATE_TRAJECTORY", parent=self, master=self.current_master)

				### The START_CONCURRENT_SIMULATION event occurs
				PluginManager.trigger_event("START_CONCURRENT_SIMULATION", parent=self, master=self.current_master)

				### future call is required because the simulator is flattened during the execution of the strategy 3
				wx.FutureCall(1, PluginManager.trigger_event, 'START_DIAGRAM', parent=self, master=self.current_master)

				### clear all log file
				for fn in [f for f in os.listdir(gettempdir()) if f.endswith('.devsimpy.log')]:
					os.remove(os.path.join(gettempdir(),fn))

				self.thread = simulator_factory(self.current_master, self.selected_strategy, self.prof, self.ntl, self.verbose, self.dynamic_structure_flag, self.real_time_flag)
				self.thread.setName(self.title)

				### if simulation model has no connection or no generators, no need to simulate
				if self.thread.end_flag:
					self.OnTimer(event)
				else:
					self.timer.Start()

				### timer for real time
				if self.real_time_flag: 
					self.t = timer()
		
			else:
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

		if self.thread:
			self.thread.terminate(False)

		self.timer.Stop()
		
		wx.Bell()

		self._gauge.SetValue(0)
		self.statusbar.SetBackgroundColour('')
		printOnStatusBar(self.statusbar, {0:_('Interrupted')})
		printOnStatusBar(self.statusbar, {1:""})
		if self.statusbar.GetFieldsCount() > 2:
			printOnStatusBar(self.statusbar, {2:""})

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

		printOnStatusBar(self.statusbar, {0:_('Suspended')})

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
			timeLast = self.thread.model.timeLast
			if isinstance(self.thread.model.timeLast, tuple):
				timeLast = timeLast[0]

			self.count = (timeLast/self.thread.model.FINAL_TIME)*100

			wx.CallAfter(self._gauge.SetValue,int(self.count))

		### if simulation is over
		if self.thread.end_flag:

			### update the status of buttons
			self._btn1.Enable(True)
			self._btn2.Disable()
			self._btn3.Disable()
			self._value.Enable(not self.ntl)
			self._cp.Enable()

			### check if gauge is full (can appear if timer is too slow)
			if self.count != 100 or self.ntl:
				self.count = 100
				wx.CallAfter(self._gauge.SetValue, int(self.count))

			### update the status bar
			self.statusbar.SetBackgroundColour('')
			printOnStatusBar(self.statusbar, {0:_("Completed!"), 1:self.GetClock()})
			
			### is no time limit add some informations in status bar
			if not self.ntl:
				if self.statusbar.GetFieldsCount() > 2:
					printOnStatusBar(self.statusbar, {2:str(100)+"%"})

			### stop the timer
			self.timer.Stop()

		### if the simulation is not suspended
		elif not self.thread.thread_suspend:

			### udpate the status bar
			if self.statusbar.GetBackgroundColour() != 'GREY': 
				self.statusbar.SetBackgroundColour('GREY')
			wx.CallAfter(printOnStatusBar,self.statusbar, {0:_("Processing..."), 1:self.GetClock()})

			### is no time limit, add some information in status bar
			if not self.ntl:
				if self.statusbar.GetFieldsCount() > 2:
					wx.CallAfter(printOnStatusBar,self.statusbar, {2:str(self.count)[:4]+"%"})

			#wx.Yield()
			#wx.YieldIfNeeded()

	def GetClock(self):
		if self.real_time_flag:	
			return str(next(self.t))
		
		### clock formating
		ms = self.thread.cpu_time%1
		m, s = divmod(self.thread.cpu_time, 60)
		h, m = divmod(m, 60)
		return "%d:%02d:%02d:%03d" % (h, m, s, ms*1000)

	###
	def MsgBox(self, msg:str):
		""" Pop-up alert for empty model.
		"""
		dial = wx.MessageDialog(self,
							_('You want to simulate an empty master model!'),
							_('Simulation Manager'),
							wx.OK|wx.ICON_EXCLAMATION)

		if (dial.ShowModal() == wx.ID_OK) and isinstance(self.parent, wx.Frame):
			self.PrepareDestroyWin()
			### destroy the frame
			self.Destroy()
		else:
			return

	def SetFields(self):
		"""
		"""
		if wx.VERSION_STRING < '4.0':
			self.statusbar.SetFields([""]*self.statusbar.GetFieldsCount())
		else:
			printOnStatusBar(self.statusbar, {i:'' for i in range(self.statusbar.GetFieldsCount())})

	def PrepareDestroyWin(self):
		""" To destroy the simulation frame.
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
			for i in range(self.parent.menuBar.GetMenuCount()):
				self.parent.menuBar.EnableTop(i,True)

			### other tab diagram enabled
			nb2 = self.parent.GetDiagramNotebook()
			for p in range(nb2.GetPageCount()):
				## pour tout les tab non selectionner
				if p != nb2.GetSelection():
					nb2.GetPage(p).Enable()

		except Exception:
			#sys.stdout.write(_("Empty mode over\n"))
			pass

	def OnQuit(self, event):
		""" When the simulation are stopping.
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
				self.thread.terminate(False)
				self.PrepareDestroyWin()
			else:
				self.thread.resume_thread()

		else:
			self.PrepareDestroyWin()

		event.Skip()

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
			paths = [a for a in trace if a.split(',')[0].strip().startswith('File')]
	
			### find if DOMAIN_PATH is in the first file path of the trace
			path = paths[-1]
			devs_error = DOMAIN_PATH in path or HOME_PATH not in path
				
		except Exception as info:
			sys.stdout.write(_("Error in ErrorManager: %s"%info))
	
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
					self.PrepareDestroyWin()
					self.Destroy()
				else:
				### if user want to correct error through an editor, we stop simulation process for trying again after the error is corrected.
					self.OnStop(event)
		else:
			raise MyBad(msg)

class SimulationDialogPanel(Base, wx.Panel):
	""" Simulation Dialog Panel 
	""" 
	def __init__(self, parent, id, title):
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
		
		Base.__init__(self, parent, id, title)
		#self.SetMaster(master)

	def SetMaster(self, master):
		Base.SetMaster(self, master)

	def GetMaster(self):
		return Base.GetMaster(self)

class SimulationDialogFrame(Base, wx.Frame):
	""" SimulationDialog(parent, id, title, master)

		Frame or Panel with progress bar
	"""

	def __init__(self, parent, id, title):
		""" Constructor
		"""

		assert(isinstance(parent, wx.Frame))
		
		wx.Frame.__init__(self, parent, id, title, style= wx.DEFAULT_FRAME_STYLE)

		# disable the roll out of the frame
		self.SetMinSize(self.GetSize())

		self.panel = wx.Panel(self)

		wx.CallAfter(self.CreateBar)
		
		Base.__init__(self, parent, id, title)

		self.__set_properties()

	def __set_properties(self):
		icon = wx.EmptyIcon() if wx.VERSION_STRING < '4.0' else wx.Icon()
		icon.CopyFromBitmap(wx.Bitmap(os.path.join(ICON_PATH_16_16, "simulation.png"), wx.BITMAP_TYPE_ANY))
		self.SetIcon(icon)
		self.Center()
	
	def SetMaster(self, master):
		Base.SetMaster(self, master)

	def GetMaster(self):
		return Base.GetMaster(self)
		
def SimulationDialog(*args):
	parent = args[0]
	if isinstance(parent, wx.Panel):
		return SimulationDialogPanel(*args)
	else:
		return SimulationDialogFrame(*args)

### ------------------------------------------------------------
class TestApp(wx.App):
	""" Testing application
	"""

	def OnInit(self):

		builtins.__dict__['PYDEVS_SIM_STRATEGY_DICT'] = {'original':'SimStrategy1', 'bag-based':'SimStrategy2', 'direct-coupling':'SimStrategy3'}
		builtins.__dict__['PYPDEVS_SIM_STRATEGY_DICT'] = {'classic':'SimStrategy4', 'distribued':'SimStrategy5', 'parallel':'SimStrategy6'}
		
		import gettext
		#import DomainInterface.MasterModel

		builtins.__dict__['ICON_PATH_16_16']=os.path.join('icons','16x16')
		builtins.__dict__['DEFAULT_SIM_STRATEGY'] = 'original'
		builtins.__dict__['DYNAMIC_STRUCTURE'] = False
		builtins.__dict__['REAL_TIME'] = False
		builtins.__dict__['VERBOSE'] = False
		builtins.__dict__['NTL'] = False
		builtins.__dict__['_'] = gettext.gettext

		self.frame = SimulationDialog(wx.Frame(), wx.NewIdRef(), 'Simulator')
		#self.frame.SetMaster(DomainInterface.MasterModel.Master())
		self.frame.Show()
		return True

	def OnQuit(self, event):
		self.Close()

if __name__ == '__main__':
	app = TestApp(0)
	app.MainLoop()