# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Factory.py ---
#                    --------------------------------
#                            Copyright (c) 2020
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 09/10/20
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

import gettext
_ = gettext.gettext

if builtins.__dict__.get('GUI_FLAG',True):
    import wx

import threading
import sys
import traceback

# to send event
from pubsub import pub

from Utilities import playSound, NotificationMessage
from Patterns.Strategy import *
from Decorators import hotshotit

def simulator_factory(model, strategy, prof, ntl, verbose, dynamic_structure_flag, real_time_flag):
	""" Preventing direct creation for Simulator
        disallow direct access to the classes
	"""

	### find the correct simulator module depending on the
	for pydevs_dir, filename in list(builtins.__dict__['DEVS_DIR_PATH_DICT'].items()):
		if pydevs_dir == builtins.__dict__['DEFAULT_DEVS_DIRNAME']:
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

		def simulate(self, T = 100000000):
			""" Simulate for T
			"""
			return self.__algorithm.simulate(T)

		def getMaster(self):
			""" Get the master DEVS model.
			"""
			return self.model

		def setMaster(self, model):
			""" Set the DEVS master model.
			"""
			self.model = model

		def setAlgorithm(self, s):
			""" Set the simulation algo.
			"""
			self.__algorithm = s

		def getAlgorithm(self):
			""" Get the selected simlation algo.
			"""
			return self.__algorithm

	class SimulationThread(threading.Thread, Simulator):
		"""
			Thread for DEVS simulation task.
		"""

		def __init__(self, model=None, strategy='', prof=False, ntl=False, verbose=False, dynamic_structure_flag=False, real_time_flag=False):
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

			#self.deamon = True

			self.end_flag = False
			self.thread_suspend = False
			self.sleep_time = 0.0
			self.thread_sleep = False
			self.cpu_time = -1

			self.start()

		@hotshotit
		def run(self):
			""" Run thread.
			"""

			### define the simulation strategy
			args = {'simulator':self}
			### TODO: isinstance(self, PyDEVSSimulator)
			if DEFAULT_DEVS_DIRNAME == "PyDEVS":
				cls_str = eval(PYDEVS_SIM_STRATEGY_DICT[self.strategy])
			else:
				cls_str = eval(PYPDEVS_SIM_STRATEGY_DICT[self.strategy])

			self.setAlgorithm(cls_str(*(), **args))

			while not self.end_flag:
				### traceback exception engine for .py file
				try:
					self.simulate(self.model.FINAL_TIME)
				except Exception as info:
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
					if builtins.__dict__.get('GUI_FLAG',True):
						if wx.VERSION_STRING < '2.9':
							wx.CallAfter(pub.sendMessage,"error", msg)
						else:
							wx.CallAfter(pub.sendMessage,"error", msg=msg)

						### error sound
						wx.CallAfter(playSound, SIMULATION_ERROR_SOUND_PATH)
				else:
					for m in [a for a in list(self.model.getFlatComponentSet().values()) if hasattr(a, 'finish')]:
						### call finished method
						if builtins.__dict__.get('GUI_FLAG',True):
							#if wx.VERSION_STRING < '2.9':
							try:
								pub.sendMessage('%d.finished'%(id(m)))
							except Exception:
								try:
									pub.sendMessage('%d.finished'%(id(m)), msg="")
								except:
									pass
						else:
							m.finish(None)

					### resionly for displayed application (-nogui)
					if builtins.__dict__.get('GUI_FLAG',True):
						if self.prof:
							NotificationMessage(_("Information"), _("Profiling report is available on Options->Profile"), None, timeout=5)

						wx.CallAfter(playSound, SIMULATION_SUCCESS_SOUND_PATH)

			self.end_flag = True
			
		def set_sleep(self, sleeptime):
			""" Set the sleep.
			"""
			self.thread_sleep = True
			self._sleeptime = sleeptime

		def suspend(self):
			""" Suspend the Thread.
			"""
			#main_thread = threading.currentThread()
			#for t in threading.enumerate():
			#	t.thread_suspend = True

			self.thread_suspend = True

		def resume_thread(self):
			""" Resume the Thread.
			"""
			self.thread_suspend = False

	return SimulationThread(model, strategy, prof, ntl, verbose, dynamic_structure_flag, real_time_flag)