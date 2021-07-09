# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Decorators.py ---
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

import os
import sys
import time
from datetime import datetime
import threading
from tempfile import gettempdir
import time
import cProfile, pstats, io

import gettext
_ = gettext.gettext

if builtins.__dict__.get('GUI_FLAG',True):
	import wx
	if wx.VERSION_STRING < '4.0':
		import wx.aui
		AuiFloatingFrame = wx.aui.AuiFloatingFrame
	else:
		import wx.lib.agw.aui.framemanager
		AuiFloatingFrame = wx.lib.agw.aui.framemanager.AuiFloatingFrame

	from pubsub import pub

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
			prof_name = os.path.join(gettempdir(),"%s_%s_%s%s"%(func.__name__, label, date_time ,'.prof'))

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
		mainW = wx.GetApp().GetTopWindow()

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
			message = _('Please wait..')

		progress_dlg = wx.ProgressDialog(title, message, style=wx.PD_APP_MODAL|wx.PD_CAN_ABORT)

		thread = ThreadWithReturnValue(target = f, args = args)
		thread.start()

		### isAlive is deprecated since python 3.9		
		while thread.isAlive() if hasattr(thread,'isAlive') else thread.is_alive():

			if progress_dlg.WasCancelled() or progress_dlg.WasSkipped():
				thread.kill()
			else:
				wx.MilliSleep(300)
				progress_dlg.Pulse(thread.getLog())
				wx.SafeYield()

		progress_dlg.Destroy()

		return thread.join()

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
