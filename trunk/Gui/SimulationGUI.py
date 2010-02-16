# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# SimulationGUI.py ---
#                     --------------------------------
#                        Copyright (c) 2010
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 1/01/10 
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
import os, sys, copy
import threading, time

from DEVSKernel.FastSimulator import Simulator
	
def IsAllDigits(str):
	""" Is the given string composed entirely of digits? """
	import string
	match = string.digits+'.'
	ok = 1
	for letter in str:
		if letter not in match:
			ok = 0
			break
	return ok
	
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
			wx.MessageBox(_("A field must contain some positive numbers!"),_("Error"))
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

#-----------------------------------------------------------------
class SimulationDialog(wx.Frame, wx.Panel):
	""" SimulationDialog(parent, id, title, master)
		
		Frame or Panel with progress bar
	"""

	def __init__(self, parent, id, title, master):
		""" Constructor
		"""

		if isinstance(parent, wx.Panel):
			wx.Panel.__init__(self, parent, id)
			self.SetBackgroundColour(wx.NullColour)
			self.panel = self
			# status bar de l'application principale
			self.statusbar = parent.GetTopLevelParent().statusbar
		else:
			wx.Frame.__init__(self, parent, id, title, size=(260,160),
			style= wx.DEFAULT_FRAME_STYLE
			|wx.STAY_ON_TOP        # forces the window to be on top / non-modal
			|wx.CLOSE_BOX
			|wx.MINIMIZE_BOX
			|wx.CAPTION)
			
			self.panel = wx.Panel(self, wx.ID_ANY)
			self.statusbar = parent.statusbar

			self.__set_properties()
		
		# local copy
		self.parent = parent
		self.master = master

		# definition du thread, du timer et du compteur pour les % de simulation
		self.thread = None
		self.timer = wx.Timer(self, wx.NewId())
		self.count = 10.0
		self.stdioWin = None

		self.panel1 = wx.Panel(self.panel, wx.ID_ANY, name = "SimTime")
		self.panel3 = wx.Panel(self.panel, wx.ID_ANY, name = "panel_options")
		self.panel2 = wx.Panel(self.panel, wx.ID_ANY, name = "buttons")
		self.panel4 = wx.Panel(self.panel, wx.ID_ANY, name = "panel_gauge")
		self.panel5 = wx.Panel(self.panel, wx.ID_ANY, name = "panel_bottom")
		
		self.text = wx.StaticText(self.panel1, wx.ID_ANY, _('Final time'))
		self.value = wx.TextCtrl(self.panel1, wx.ID_ANY, str(float(self.master.FINAL_TIME)), validator=TextObjectValidator())
		self.btn1 = wx.Button(self.panel2, wx.NewId(), _('Run'))
		self.btn2 = wx.Button(self.panel2, wx.NewId(), _('Stop'))
		self.btn3 = wx.Button(self.panel2, wx.NewId(), _('Suspend'))
		self.btn4 = wx.Button(self.panel2, wx.NewId(), _('Log'))
		self.gauge = wx.Gauge(self.panel4, wx.ID_ANY, 100, size=(-1, 25), style = wx.GA_HORIZONTAL)
		self.cp = wx.CollapsiblePane(self.panel5, label=_("Setting"), style = wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
		self.cb1 = wx.CheckBox(self.panel3, wx.ID_ANY, _('Fault Simulation'), name = 'check_fault_sim')
		self.cb2 = wx.CheckBox(self.panel3, wx.ID_ANY, _('Verbose'), name = 'check_verbose')

		self.__do_layout()
		self.__set_events()
		
	def __set_properties(self):
		_icon = wx.EmptyIcon()
		_icon.CopyFromBitmap(wx.Bitmap(os.path.join(ICON_PATH_20_20, "simulation.png"), wx.BITMAP_TYPE_ANY))
		self.SetIcon(_icon)
		self.Center()

		# empeche d'etirer la frame
		self.SetMaxSize(wx.Size(260,220))
		self.SetMinSize(wx.Size(260,160))

	def __do_layout(self):

		vbox_top = wx.BoxSizer(wx.VERTICAL)
		vbox_body = wx.BoxSizer(wx.VERTICAL)
		
		#panel 1
		grid1 = wx.GridSizer(1, 2)
		grid1.Add(self.text, 0,  wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
		grid1.Add(self.value, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL)
		self.panel1.SetSizer(grid1)
		vbox_body.Add(self.panel1, 0, wx.EXPAND, 9)
		
		# panel2
		grid2 = wx.GridSizer(2, 2, 2, 2)
		grid2.Add(self.btn1, 0,  wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
		grid2.Add(self.btn3, 0,  wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
		grid2.Add(self.btn2, 0,  wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
		grid2.Add(self.btn4, 0,  wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
		self.panel2.SetSizer(grid2)
		vbox_body.Add(self.panel2, 0, wx.EXPAND, 9)
		
		# panel4
		hbox1 = wx.BoxSizer(wx.HORIZONTAL)
		hbox1.Add(self.gauge, 1, wx.EXPAND, 9)
		self.panel4.SetSizer(hbox1)
		vbox_body.Add(self.panel4, 0, wx.EXPAND, 9)
		
		# panel5
		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		hbox2.Add(self.cp)
		self.panel5.SetSizer(hbox2)
		vbox_body.Add(self.panel5, 1, wx.EXPAND, 9)
		
		# panel3
		#sbox = wx.BoxSizer(wx.VERTICAL)
		vbox3 = wx.BoxSizer(wx.VERTICAL)
		grid3 = wx.GridSizer(1, 1, 0, 5)
		grid3.Add(self.cb1)
		grid3.Add(self.cb2)
		vbox3.Add(grid3)
		#sbox.Add(vbox3, 0, wx.TOP|wx.EXPAND)
		
		self.panel3.SetSizer(vbox3)
		vbox_body.Add(self.panel3, 0, wx.TOP|wx.EXPAND)

		# fin panel
		vbox_top.Add(vbox_body, 0, wx.EXPAND, 9)
		self.panel.SetSizer(vbox_top)

		self.text.SetFocus()
		self.btn1.SetDefault()
		self.btn2.Disable()
		self.btn3.Disable()
		self.panel3.Hide()
		
	def __set_events(self):

		# gestionnaires d'evenements
		self.Bind(wx.EVT_BUTTON, self.OnOk, self.btn1)
		self.Bind(wx.EVT_BUTTON, self.OnStop, self.btn2)
		self.Bind(wx.EVT_BUTTON, self.OnSuspend, self.btn3)
		self.Bind(wx.EVT_BUTTON, self.OnViewLog, self.btn4)
		self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnExtend, self.cp)
		self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
		self.Bind(wx.EVT_TEXT,self.OnText, self.value)
		self.Bind(wx.EVT_CLOSE, self.OnQuit)

	###
	def OnText(self,event):
		self.gauge.SetValue(0)

	###
	def OnExtend(self, event):
		""" Extend windows for more options
		"""

		panel_options = self.FindWindowByName("panel_options")
		if not panel_options.IsShown():
			# si les instructions sont iversées ca ne fonctionne pas sous Win
			panel_options.Show(True)
			self.SetSizeWH(260, 220)
		else:
			panel_options.Show(False)
			self.SetSizeWH(260, 160)
			
	###
	def OnViewLog(self, event):
		"""	When View button is clicked
		"""

		if self.stdioWin !=None:
			self.stdioWin.frame.Show()
	
	###
	def OnOk(self, event):
		""" When Run button is clicked
		"""

		if self.value.GetValidator().Validate(self.value):	
			# si instance de simulation dans le panel de gauche et 
			# si il n'y a pas eu de suspend alors
			# il faut definir le model a simuler
			if isinstance(self.parent,wx.Panel) and self.gauge.GetValue()==0:
				mainWindow = self.parent.GetTopLevelParent()
				nb = mainWindow.nb2
				actuel = nb.GetSelection()
				diagram = nb.GetPage(actuel).diagram
				#d = copy.copy(diagram)
				d = diagram
				l = copy.copy(d.shapes)
				self.master = diagram.makeDEVSConnection(d,l)
				# redirection du stdout ici dans le cas du Panel (sinon dans OnSimulation)
				sys.stdout = mainWindow.stdioWin
				
			# test si le modele et bien charge	
			if (self.master == None) or (self.master.componentSet == []):
				return self.MsgBoxEmptyModel()
						
			# stockage des options de simulation en passant par le Master
			self.master.VERBOSE = self.FindWindowByName("check_verbose").IsChecked()
			self.master.FAULT_SIM = self.FindWindowByName("check_fault_sim").IsChecked()
			# stockage du temps de simulation dans le master
			self.master.FINAL_TIME = float(self.value.GetValue())

			self.btn1.Enable(False)
			self.btn2.Enable(True)
			self.btn3.Enable(True)
			self.value.Disable()
			self.gauge.SetValue(0)
			self.statusbar.SetBackgroundColour('')
			self.statusbar.SetStatusText("", 1)
			self.statusbar.SetStatusText("", 2)
			 
			if (self.thread is None) or (not self.timer.IsRunning()):
				
				self.thread = SimulationThread(self.master)

				## si le modele n'a pas de couplage, ou si pas de generateur: alors pas besoin de simuler
				if self.thread.end_flag:
					self.master.timeLast=self.master.FINAL_TIME
					self.OnTimer(event)
				else:
					self.timer.Start(100)
			else:
				self.thread.resume_thread()
			
			if self.count >= 100: return
			
			# aucune possibilité d'interagir avec le modele
			#self.parent.Enable(False)
	###
	def OnStop(self, event):
		""" When Stop button is cliked
		"""

		self.btn1.Enable(True)
		self.btn2.Enable(False)
		self.btn3.Enable(False)
		self.value.Enable(True)
		
		self.thread.terminate()
		self.timer.Stop()
		wx.Bell()
			
		self.gauge.SetValue(0)
		self.statusbar.SetBackgroundColour('')
		self.statusbar.SetStatusText(_('Task Interrupted'), 0)
		self.statusbar.SetStatusText("", 1)
		self.statusbar.SetStatusText("", 2)
	
	###
	def OnSuspend(self, event):
		""" When Stop button is cliked
		"""
		
		self.btn1.Enable(True)
		self.btn2.Enable(True)
		self.btn3.Enable(False)
		
		self.thread.suspend()
		
		if self.count == 0 or self.count >= 100 or not self.timer.IsRunning():
			return

		self.statusbar.SetStatusText(_('Task in Suspends'))
		# possibilité d'interagir avec le modele
		#self.parent.Enable(True)
		wx.Bell()
		
	###
	def OnTimer(self, event):
		""" Give the pourcentage of simulation progress
		"""
		
		self.count = (self.master.timeLast/self.master.FINAL_TIME)*100
	
		if round(self.count)>=100.0:
			self.gauge.SetValue(100)
			self.timer.Stop()
			self.btn1.Enable(True)
			self.btn2.Enable(False)
			self.btn3.Enable(False)
			self.value.Enable(True)
			self.statusbar.SetBackgroundColour('')
			self.statusbar.SetStatusText(_("Simulation Completed"), 0)
			self.statusbar.SetStatusText(str(100)+"%", 2)
		else:
			self.gauge.SetValue(self.count)
			# affiche dans l'application les %
			self.statusbar.SetBackgroundColour('grey')
			self.statusbar.SetStatusText(_("Simulation process"), 0)
			self.statusbar.SetStatusText(str(self.count)[:4]+"%", 2)
		
	###
	def MsgBoxEmptyModel(self):
		""" Pop-up alert for empty model
		"""
		dial = wx.MessageDialog(self, _('You want to simulate an empty master model!'), _('Info'), wx.OK)
		if (dial.ShowModal() == wx.ID_OK) and (isinstance(self.parent, wx.Frame)):
			self.DestroyWin()
		else:
			return

	def DestroyWin(self):
		""" To destroy the simulation frame
		"""
		try:
			self.statusbar.SetBackgroundColour('')
			self.statusbar.SetStatusText("", 0)
			self.statusbar.SetStatusText("", 1)
			self.statusbar.SetStatusText("", 2)
		except Exception, info:
			#sys.stdout.write(_("Empty 2 mode \n"))
			pass
		
		try:
			self.parent.stdioWin.frame.Show(False)
		except:
			pass
			
		try:
		## panel gauche inaccessible
			self.parent.nb1.Enable()
		
			## menu inaccessible			
			self.parent.tb.Enable()
			for i in range(self.parent.menuBar.GetMenuCount()):
				self.parent.menuBar.EnableTop(i,True)
			
			## autre tab inaccessible
			for p in range(self.parent.nb2.GetPageCount()):
				## pour tout les tab non selectionner
				if p != self.parent.nb2.GetSelection():
					self.parent.nb2.GetPage(p).Enable()
		except Exception, why:
			#sys.stdout.write(_("Empty mode over\n"))
			pass

		self.Destroy()
		
	def OnQuit(self, event):
		""" When the simulation are stopping
		"""
		# si la simulation est en cours
		if self.timer.IsRunning():
			#self.MakeModal(False)
			dial = wx.MessageDialog(self, _('Are you sure to stop simulation ?'), _('Question'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			self.thread.suspend()
			
			# si ok
			if dial.ShowModal()==wx.ID_YES:
				self.DestroyWin()
				self.thread.terminate()
			else:
				self.thread.resume_thread()
		else:
			self.DestroyWin()
		
#--------------------------------------------------------------
class SimulationThread(threading.Thread, Simulator):
	""" SimulationThread(model)
		
		Thread for DEVS simulation task
	"""
	
	def __init__(self, model):
		""" Constructor
		"""
		threading.Thread.__init__(self)
		Simulator.__init__(self, model)

		### local copy
		self.model = model

		self.end_flag = False
		self.thread_suspend = False
		self.sleep_time = 0.0
		self.thread_sleep = False
		
		self.start()
		
	def run(self):
		""" Run thread
		"""

		# Initialize the model --- set the simulation clock to 0.
		self.send(self.model, (0, [], 0))
		
		clock = self.model.myTimeAdvance
		#clock=self.model.timeNext

		# Main loop repeatedly sends $(*,\,t)$ messages to the model's root DEVS.
		while clock <= self.model.FINAL_TIME and self.end_flag == False:
			
			##Optional sleep
			if self.thread_sleep:
				time.sleep(self._sleeptime)
			##Optional suspend
			while self.thread_suspend:
				time.sleep(1.0)
			
			# calculate how much time has passed so far
			if self.model.VERBOSE: sys.stdout.write("\n"+"* "* 10+"CLOCK : %f \n" % clock)

			self.send(self.model, (1, {}, clock))
			
			clock = self.model.myTimeAdvance
			#clock=self.model.timeNext

		self.terminate()
			
	def terminate(self):
		""" Thread termination routine 
		"""

		self.end_flag = True

		filename = os.path.join(HOME_PATH,'sounds', 'Simulation-Success.wav')
		self.sound = wx.Sound(filename)
		if self.sound.IsOk():
			self.sound.Play(wx.SOUND_ASYNC)
	
	def set_sleep(self, sleeptime):
		self.thread_sleep = True
		self._sleeptime = sleeptime

	def suspend(self):
		self.thread_suspend=True
 
	def resume_thread(self):
		self.thread_suspend=False

# ------------------------------------------------------------
class TestApp(wx.App):
	""" Application composed by the Frame progress bar
	"""

	def OnInit(self):
		self.frame = SimulationDialog(None, wx.ID_ANY, 'Simulator', None)
		self.frame.Show(True)
		return True
	
	def OnQuit(self, event):
		self.Close()
		
if __name__ == '__main__':

	#try:
		#import wxversion
		#wxversion.select('2.8')
	#except:
		#pass

	#if wx.Platform == '__WXMSW__':
		#sys.path.append(os.path.dirname(os.getcwd()))
	#else:
		#for spath in [os.pardir+os.sep]:
			#if not spath in sys.path: sys.path.append(spath)

	app = TestApp(0)
	app.MainLoop()
	