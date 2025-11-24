#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###############################################################################
# simulator.py --- Classes and Tools for 'Kafka' DEVS Model Spec
#                     --------------------------------
#                            Copyright (c) 2025
#                            Laurent Capocchi
#							 SPE UMR CNRS 6134
#                       Corsican University (France)
#                     --------------------------------
# Version                                        last modified: 11/24/2025
###############################################################################
# NOTES:
# To mesure the performance of the simulator, one can use:
# conda install -c anaconda snakeviz
# python -m CProfile -o profile.out devsimpy-nogui.py <model.dsp> 100 && snakeviz profile.out 
###############################################################################

from itertools import *
import builtins

from DEVSKernel.KafkaDEVS.DEVS import CoupledDEVS

### avec ce flag les simulation en nogui sont plus rapides
ENABLE_SIM_LOGS = getattr(builtins,'GUI_FLAG', True)

###############################################################################
# SIMULATOR CLASSE
###############################################################################

class Simulator:
	""" Simulator(model)

		Associates a hierarchical DEVS model with the simulation engine.
		To simulate the model, use simulate(T) strategy method.
	"""

	###
	def __init__(self, model = None):
		"""Constructor.

		model is an instance of a valid hierarchical DEVS model. The
		constructor stores a local reference to this model and augments it with
		time variables required by the simulator.
		"""

		self.model = model
		self.__augment(self.model)

	###
	def __augment(self, d = None):
		"""Recusively augment model d with time variables.
		"""

		# {\tt timeLast} holds the simulation time when the last event occured
		# within the given DEVS, and (\tt myTimeAdvance} holds the amount of time until
		# the next event.
		d.timeLast = d.myTimeAdvance = 0.

		if isinstance(d, CoupledDEVS):
			# {\tt eventList} is the list of pairs $(tn_d,\,d)$, where $d$ is a
			# reference to a sub-model of the coupled-DEVS and $tn_d$ is $d$'s
			# time of next event.
			for subd in d.componentSet:
				self.__augment(subd)
