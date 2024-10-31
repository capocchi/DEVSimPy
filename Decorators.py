# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Decorators.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 2.0                                        last modified: 11/01/24
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

import os
import sys
import time
from datetime import datetime
import threading
from tempfile import gettempdir
import time
import cProfile, pstats, io

if builtins.__dict__.get('GUI_FLAG', True):
	import wx
	if wx.VERSION_STRING < '4.0':
		import wx.aui
		AuiFloatingFrame = wx.aui.AuiFloatingFrame
	else:
		import wx.lib.agw.aui.framemanager
		AuiFloatingFrame = wx.lib.agw.aui.framemanager.AuiFloatingFrame

	from pubsub import pub

	from Utilities import getTopLevelWindow

	_ = wx.GetTranslation
	
def cond_decorator(flag, dec):
	def decorate(fn):
		return dec(fn) if flag else fn
	return decorate

class memoize:
    # from http://avinashv.net/2008/04/python-decorators-syntactic-sugar/
    def __init__(self, function):
        self.function = function
        self.memoized = {}

    def __call__(self, *args):
        try:
            return self.memoized[args]
        except KeyError:
            self.memoized[args] = self.function(*args)
            return self.memoized[args]

def hotshotit(func):
	def wrapper(*args, **kw):
		sim_thread = args[0]
		prof = sim_thread.prof
		### if profiling check-box is checked in the simulationDialog
		if prof:
			
			### name of .prof file
			label = sim_thread.model.getBlockModel().label
			now = datetime.now() # current date and time
			date_time = now.strftime('%m-%d-%Y_%H-%M-%S')
			prof_name = os.path.join(os.path.realpath(gettempdir()),"%s_%s_%s%s"%(func.__name__, label, date_time ,'.prof'))

			### profiling section with cProfile
			pr = cProfile.Profile()
			pr.enable()
			r = func(*args, **kw)
			pr.disable()
			#Sort the statistics by the cumulative time spent in the function
			sortby = 'cumulative'
			ps = pstats.Stats(pr).sort_stats(sortby)
			ps.dump_stats(prof_name)

		else:
			r = func(*args, **kw)
		return r
	return wrapper

def run_in_thread(fn):
	''' decorator to execute a method in a specific thread
	'''

	def run(*k, **kw):
		t = threading.Thread(target=fn, args=k, kwargs=kw)
		t.start()
	return run

def BuzyCursorNotification(f):
	""" Decorator which give the buzy cursor for long process
	"""
	def wrapper(*args):
			if builtins.__dict__.get('GUI_FLAG',True):
				wait = wx.BusyCursor()
				#wx.SafeYield()
			r =  f(*args)
			if builtins.__dict__.get('GUI_FLAG',True):
				del wait
			return r
	return wrapper

# allows  arguments for a decorator
decorator_with_args = lambda decorator: lambda *args, **kwargs: lambda func: decorator(func, *args, **kwargs)

@decorator_with_args
def StatusBarNotification(f, arg):
	""" Decorator which give information into status bar for the load and the save diagram operations
	"""

	def wrapper(*args):

		# main window
		mainW = getTopLevelWindow()

		### find if detachedFrame exists
		for win in [w for w in mainW.GetChildren() if w.IsTopLevel()]:
			if win.IsActive() and isinstance(win, wx.Frame) and not isinstance(win, wx.aui.AuiFloatingFrame if wx.VERSION_STRING < '4.0' else wx.lib.agw.aui.framemanager.AuiFloatingFrame):
				mainW = win

		r = f(*args)

		if hasattr(mainW, 'statusbar'):
			diagram = args[0]
			fn = os.path.basename(args[-1])
			txt = arg

			mainW.statusbar.SetStatusText('%s %sed'%(fn, txt), 0)
			mainW.statusbar.SetStatusText(diagram.last_name_saved, 1)
			mainW.statusbar.SetStatusText('', 2)

		return r

	return wrapper

class ThreadWithReturnValue(threading.Thread):
	""" https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
	"""
	def __init__(self, *args, **kwargs): 
		super(ThreadWithReturnValue, self).__init__(*args, **kwargs) 
		#self._return = None
		self.killed = False
		self._log = ""
		self._status = ""
		pub.subscribe(self.my_listener, "to_progress_diag")

	def start(self): 
		self.__run_backup = self.run 
		self.run = self.__run       
		threading.Thread.start(self)
		self._status = 'alive'
	
	def __run(self): 
		sys.settrace(self.globaltrace) 
		self._return = self.__run_backup() 
		self.run = self.__run_backup 

	def globaltrace(self, frame, event, arg): 
		if event == 'call': 
			return self.localtrace 
		else: 
			return None
	
	def localtrace(self, frame, event, arg): 
		if self.killed: 
			if event == 'line': 
				raise SystemExit()
		return self.localtrace 
	
	def my_listener(self, message, arg2=None):
		"""
		Listener function
		"""
		self._log = message
		if arg2 == 'stop':
			self.kill()
		elif arg2 is not None:
			self._status = arg2

	def getStatus(self):
		return self._status

	def getLog(self):
		return self._log

	def kill(self): 
		self.killed = True

	# def run(self):
	# 	if self._target is not None:
	# 		try:
	# 			self._return = self._target(*self._args, **self._kwargs)
	# 		except Exception as e:
	# 			self._return = e
			
	# def join(self):
	# 	if not isinstance(self._return, Exception):
	# 		threading.Thread.join(self)
	# 	return self._return

@decorator_with_args
def ProgressNotification(f, arg):
	def wrapper(*args):

		title = arg
		new_path = args[-1]
		if isinstance(new_path, str) and os.path.isfile(new_path):
			message = _("Loading %s ...")%os.path.basename(new_path)
		else:
			message = _('Please wait...')

		progress_dlg = wx.ProgressDialog(title, message, style=wx.PD_APP_MODAL|wx.PD_CAN_ABORT)

		thread = ThreadWithReturnValue(target = f, args = args)
		thread.start()

		cancelled = False
		### isAlive is deprecated since python 3.9		
		while thread.isAlive() if hasattr(thread, 'isAlive') else thread.is_alive() and not cancelled:

			if progress_dlg.WasCancelled() or progress_dlg.WasSkipped():
				thread.kill()
				cancelled = True
				break
			else:
				wx.MilliSleep(300)
				progress_dlg.Pulse(thread.getLog())
				wx.SafeYield()

		progress_dlg.Destroy()

		# Vérifier si le thread a été annulé et gérer la fin du thread
		if not cancelled:
			return thread.join()
		else:
			return None  # Retourner None en cas d'annulation pour indiquer l'interruption

	return wrapper

def print_timing(func):
	def wrapper(*arg):
		t1 = time.time()
		res = func(*arg)
		t2 = time.time()
		final_t = (t2-t1)*1000.0
		return res
	return wrapper

def Pre_Undo(f):
	def wrapper(*args):

		diagram = args[0]
		diagram.Undo()
		r = f(*args)

		return r
	return wrapper

def Post_Undo(f):
	def wrapper(*args):

		diagram = args[0]
		r = f(*args)
		diagram.Undo()

		return r
	return wrapper

def redirectStdout(f):
	def wrapper(*args):
		stdout = sys.stdout
		output = ""
		try:
			sys.stdout = io.StringIO()
			f(*args)
			output = sys.stdout.getvalue()
		finally:
			sys.stdout = stdout
		return output
	return wrapper

class SpinningProgressBar(wx.Frame):
    def __init__(self, parent=None, title="Spinning Progress"):
        super().__init__(parent, title=title, size=(500, 150))
        self.is_active = False  # Variable de contrôle pour la barre de progression

        # Crée le panel et le sizer
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Texte d'instruction
        self.label = wx.StaticText(panel, label="Téléchargement en cours, veuillez patienter...")
        vbox.Add(self.label, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        # Créer la barre de progression
        self.gauge = wx.Gauge(panel, range=100, style=wx.GA_HORIZONTAL)
        vbox.Add(self.gauge, flag=wx.EXPAND | wx.ALL, border=20)

        panel.SetSizer(vbox)
        self.Centre()

    def show(self):
        """Démarre la fenêtre avec la barre de progression."""
        self.is_active = True
        self.Show()
        self.Raise()  # Assure que la fenêtre est bien visible au premier plan
        self.Refresh()  # Force l'affichage de la fenêtre si elle ne s'affiche pas immédiatement
        
        # Démarre un thread pour faire tourner la barre de progression
        threading.Thread(target=self._run_spinner, daemon=True).start()

    def _run_spinner(self):
        """Méthode privée pour animer la barre pour qu'elle atteigne 100% puis revienne à zéro."""
        while self.is_active:
            for i in range(101):
                if not self.is_active:
                    break
                wx.CallAfter(self.gauge.SetValue, i)
                time.sleep(0.02)  # Remplit la barre en environ 2 secondes
            wx.CallAfter(self.gauge.SetValue, 0)  # Réinitialise la barre à zéro

    def stop(self):
        """Arrête la barre de progression et cache la fenêtre."""
        self.is_active = False
        self.Hide()  # Cache la fenêtre sans la détruire, ce qui permet de la réutiliser si besoin