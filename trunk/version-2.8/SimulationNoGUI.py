# -*- coding: utf-8 -*-

"""
Name: MakeSimulation.py
Brief descritpion:
Author(s): A-T. Luciani <atluciani@univ-corse.fr>
Version:  1.0
Last modified:
GENERAL NOTES AND REMARKS:

GLOBAL VARIABLES AND FUNCTIONS:
"""

import os
import sys
#import random
import threading
import time

from tempfile import gettempdir

import __builtin__
import traceback

def makeJS(filename):
	"""
	"""

	import Container

	a = Container.Diagram()
	if a.LoadFile(filename):
		sys.stdout.write("\nFichier charge\n")
		master = Container.Diagram.makeDEVSInstance(a)

		addInner = []
		liaison = []
		model = {}
		labelEnCours = str(os.path.basename(a.last_name_saved).split('.')[0])

		# path = os.path.join(os.getcwd(),os.path.basename(a.last_name_saved).split('.')[0] + ".js") # genere le fichier js dans le dossier de devsimpy
		# path = filename.split('.')[0] + ".js" # genere le fichier js dans le dossier du dsp charg�.

		#Position initial du 1er modele
		x = [40]
		y = [40]
		bool = True

		from Join import makeDEVSConf, makeJoin

		model, liaison, addInner = makeJoin(a, addInner, liaison, model, bool, x, y, labelEnCours)
		makeDEVSConf(model, liaison, addInner, "%s.js"%labelEnCours)
	else:
		return False

class Printer:
	"""
	Print things to stdout on one line dynamically
	"""

	def __init__(self,data):

		sys.stdout.write("\r\x1b[K"+data.__str__())
		sys.stdout.flush()

def makeSimulation(filename, T):
	"""
	"""

	import Container

	a = Container.Diagram()

	if a.LoadFile(filename):
		sys.stdout.write("\nFichier charge\n")


		try:
			master = Container.Diagram.makeDEVSInstance(a)
			#print "master -> " , master
			#print "a -> " , a
		except :
			return False
		else:
			sim = runSimulation(master,T)
			thread = sim.Run()

			# first_time = time.time()
			# while(thread.isAlive()):
				# new_time = time.time()
				# Printer(new_time - first_time)

			sys.stdout.write("\nTime : %s"%str(master.FINAL_TIME))
			sys.stdout.write("\nFin.\n")

class runSimulation:
	"""
	"""

	def __init__(self, master, time):
		""" Constructor.
		"""

		# local copy
		self.master = master
		self.time = time

		### No time limit simulation (defined in the builtin dico from .devsimpy file)
		self.ntl = __builtin__.__dict__['NTL']

		# simulator strategy
		self.selected_strategy = DEFAULT_SIM_STRATEGY

		### profiling simulation with hotshot
		self.prof = False

		# definition du thread, du timer et du compteur pour les % de simulation
		self.thread = None
		self.count = 10.0
		self.stdioWin = None

	###
	def Run(self):
		""" run simulation
		"""

		assert(self.master is not None)
		### pour prendre en compte les simulations multiples sans relancer un SimulationDialog
		### si le thread n'est pas lanc� (pas pendant un suspend)
		# if self.thread is not None and not self.thread.thread_suspend:
		diagram = self.master.getBlockModel()
		# diagram.Clean()
		# print self.master
		################################################################################################################
		######### To Do : refaire l'enregistrement du chemin d'enregistrements des resuts du to_disk ###################
		for m in self.master.componentSet:
			if str(m)=='To_Disk':
				dir_fn = os.path.dirname(diagram.last_name_saved).replace('\t','').replace(' ','')
				label = m.getBlockModel()
				m.fileName = os.path.join(dir_fn,"%s_%s"%(os.path.basename(diagram.last_name_saved).split('.')[0],os.path.basename(m.fileName)))
		################################################################################################################
		################################################################################################################

		if self.master:
			from SimulationGUI import simulator_factory

			self.master.FINAL_TIME = float(self.time)
			self.thread = simulator_factory(self.master, self.selected_strategy, self.prof, self.ntl)

		return self.thread

