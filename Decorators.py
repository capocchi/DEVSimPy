# -*- coding: utf-8 -*-

import __builtin__

import os
import sys
import time
import threading
from tempfile import gettempdir
import time
import heapq
import cPickle
import StringIO

if __builtin__.__dict__['GUI_FLAG']:
	import wx

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

hotshotProfilers = {}
def hotshotit(func):
	def wrapper(*args, **kw):
		sim_thread = args[0]
		prof = sim_thread.prof
		### if profiling check-box is checked in the simulationDialog
		if prof:
			label = sim_thread.model.getBlockModel().label

			try:
				import hotshot
				#import cProfile as hotshot
			except ImportError:
				sys.stderr.write(_("Please install hotshot module."))
				return

			global hotshotProfilers
			prof_name = os.path.join(gettempdir(),"%s_%s%s"%(func.func_name, label, '.prof'))
			profiler = hotshotProfilers.get(prof_name)
			if profiler is None:
				profiler = hotshot.Profile(prof_name)
				hotshotProfilers[prof_name] = profiler
			r = profiler.runcall(func, *args, **kw)
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
			wx.BeginBusyCursor()
			#wx.SafeYield()
			r =  f(*args)
			wx.EndBusyCursor()
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
		for win in filter(lambda w: w.IsTopLevel(), mainW.GetChildren()):
			if win.IsActive() and isinstance(win, wx.Frame) and not isinstance(win, wx.aui.AuiFloatingFrame):
				mainW = win

		r = f(*args)

		if hasattr(mainW, 'statusbar'):
			diagram = args[0]
			fn = os.path.basename(args[-1])
			txt = arg

			mainW.statusbar.SetStatusText('%s %sed'%(fn, txt), 0)
			mainW.statusbar.SetStatusText(os.path.basename(diagram.last_name_saved), 1)
			mainW.statusbar.SetStatusText('', 2)

		return r

	return wrapper

@decorator_with_args
def ProgressNotification(f,arg):
	def wrapper(*args):
		txt = arg
		new_path = args[-1]

		progress_dlg = wx.ProgressDialog(txt,
								"Loading %s ..."%os.path.basename(new_path), parent=None,
								style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
		progress_dlg.Pulse()

		#wx.SafeYield()

		r = f(*args)

		progress_dlg.Destroy()

		return r
	return wrapper

def print_timing(func):
	def wrapper(*arg):
		t1 = time.time()
		res = func(*arg)
		t2 = time.time()
		#print '%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0)
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
			sys.stdout = StringIO.StringIO()
			f(*args)
			output = sys.stdout.getvalue()
		finally:
			sys.stdout = stdout
		return output
	return wrapper
