#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# devsimpy-nogui.py --- DEVSimPy - The Python DEVS no GUI modeling and simulation software
#                     --------------------------------
#                            Copyright (c) 2025
#                              Laurent CAPOCCHI
#                        SPE - University of Corsica
#                     --------------------------------
# Version 5.1.0                                      last modified:  03/11/25
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# Bach version of DEVSimPy (whitout GUI)
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
'''

import os
import sys
import builtins
import json

from datetime import date

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

def serialize_date(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

from config import GLOBAL_SETTINGS, USER_SETTINGS

GLOBAL_SETTINGS['GUI_FLAG'] = False
GLOBAL_SETTINGS['INFINITY'] = float('inf')

builtins.__dict__.update(GLOBAL_SETTINGS)
builtins.__dict__.update(USER_SETTINGS)

### import here becaause they need buitlins !

from InteractionYAML import YAMLHandler
from StandaloneNoGUI import StandaloneNoGUI
from Utilities import get_version

__version__ = get_version()

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

def simulate(devs, duration, simu_name, is_remote, with_progress=True):
	"""Simulate the devs model during a specific duration.

	Args:
		devs (_type_): _description_
		duration (_type_): _description_
		simu_name (_type_): _description_
		is_remote (bool): _description_
	"""

	from SimulationNoGUI import makeSimulation

	if str(duration) in ('inf', 'ntl'):
		setattr(builtins, 'NTL', True)
		duration = 0.0

	if not devs:
		raise Exception(_("No model to simulate"))

	### launch simulation
	makeSimulation(master=devs, T=duration, simu_name=simu_name, is_remote=is_remote, with_progress=with_progress)

#-------------------------------------------------------------------
if __name__ == '__main__':

	import gettext
	_ = gettext.gettext

	import argparse
 	
	parser = argparse.ArgumentParser(description=_("Simulate a model unless other option is specified"))
	# required filename
	parser.add_argument("filename", help=_("dsp or yaml devsimpy file only"))
	# optional simulation_time for simulation
	parser.add_argument("simulation_time", nargs='?', help=_("Simulation time [inf|ntl]"), default='', type=str)
	# optional simulation_name for remote execution
	parser.add_argument("-remote", help=_("Remote execution"), action="store_true")
	parser.add_argument("-name", help=_("Simulation name"), type=str, default="simu")
	# optional kernel for simulation kernel
	parser.add_argument("-kernel", help=_("Simulation kernel [PyDEVS|PyPDEVS|BrokerDEVS]"), type=str, default="PyDEVS")
	# optional real time 
	parser.add_argument("-rt", help=_("Real time simulation (only for PyPDEVS)"), action="store_true")
 
	### optional zip function
	parser.add_argument("-zip", nargs='?', help=_("Export the devsimpy-nogui files into a filename file"), type=str)
 
	# non-simulation options
	group = parser.add_mutually_exclusive_group()
	group.add_argument("-js", "--javascript",help=_("Generate JS file"), action="store_true")
	group.add_argument("-json", help=_("Turn the YAML/DSP file to JSON"), action="store_true")
	group.add_argument("-tracemalloc", help=_("Trace memory allocations"), action="store_true")
	group.add_argument("-blockslist", help=_("Get the list of models in a master model"), action="store_true")
	group.add_argument("-blockargs", help=_("Parameters of an atomic model (ex. -blockargs <label of block>)"), type=str)
	parser.add_argument("-updateblockargs", help=_('''Update parameters (ex. -blockargs <label of block> -updateblockargs <"""{'<key1>':<val1>, '<key2>':<val2>, etc.}""">'''), type=str, default="")
	parser.add_argument("-docker", help=_("Add a dockerfile to the zip"), action="store_true")
	parser.add_argument("-sim_kernel", help=_("Add the sim kernel to the zip"), action="store_true")
	parser.add_argument("-with_progress", help=_("Add the progress info in the stdout trace"), action="store_true")

	args = parser.parse_args()

	if args.kernel:
		if 'PyPDEVS' in args.kernel:
			setattr(builtins,'DEFAULT_DEVS_DIRNAME','PyPDEVS_221')
			setattr(builtins, 'DEFAULT_SIM_STRATEGY', 'parallel')

			### Real time only for PyPDEVS...
			setattr(builtins, 'REAL_TIME', args.rt)
		elif 'PyDEVS' in args.kernel:
			setattr(builtins,'DEFAULT_DEVS_DIRNAME','PyDEVS')
			setattr(builtins, 'DEFAULT_SIM_STRATEGY', 'bag-based')
		elif 'BrokerDEVS' in args.kernel:
			setattr(builtins,'DEFAULT_DEVS_DIRNAME','BrokerDEVS')
			setattr(builtins, 'DEFAULT_SIM_STRATEGY', 'ms4Me')
		else:
			sys.stdout.write(_("ERROR: Invalid kernel name (must be PyDEVS, PyPDEVS or BrokerDEVS)!\n"))
			sys.exit(1)

	filename = args.filename
	
	assert os.path.exists(filename), _(f"ERROR: {filename} file does not exist!\n")
	
	yamlHandler = YAMLHandler(filename)

	assert yamlHandler.filename_is_valid, _(f"ERROR: {filename} is invalid!\n")

	if args.zip:
		# zip exportation
		assert args.zip.endswith('.zip'), _(f"ERROR: {filename} Invalid file type (must be zip file)!\n")		
		standalone = StandaloneNoGUI(filename, args.zip, add_sim_kernel=args.sim_kernel, add_dockerfile=args.docker, rt=args.rt, kernel=args.kernel)
		standalone.BuildZipPackage()

	elif args.javascript:
		# Javascript generation
		yamlHandler.getJS()

	elif args.json:
		# Just output JSON
		diagram = yamlHandler.getDiagram()
		j = diagram.toJSON()
		sys.stdout.write(json.dumps(j))
			
	elif args.blockslist:
		# get the list of models in a master model
		models_list = yamlHandler.getYAMLBlockModelsList()
		sys.stdout.write(json.dumps(models_list))

	elif args.blockargs:
		# model block parameters read or update
		label = args.blockargs
		models_list = yamlHandler.getYAMLBlockModelsList()
		assert label in models_list, _(f"ERROR: Model must belong to the list {models_list}\n")
		if args.updateblockargs:
			# model block is updated
			args = json.loads(args.updateblockargs)
			if isinstance(args,str):
				args = eval(args)
			new_args = list(args.keys())
			real_args = yamlHandler.getYAMLBlockModelArgs(label)
			if all(elem in real_args for elem in new_args):
				new_args = yamlHandler.setYAMLBlockModelArgs(label, args)
			else:
				print(f"ERROR: Invalid arguments keys for the model: {list(set(new_args) - set(real_args))}\n")
				sys.exit(1)
		else:
			new_args = yamlHandler.getYAMLBlockModelArgs(label)
			
		sys.stdout.write(json.dumps(new_args, default=serialize_date))

	else:
		### simulation mode

		### get the simulation duration
		duration_val = args.simulation_time	
		duration = float('inf') if duration_val in ('ntl', 'inf') else int(duration_val)
		
		### get the devs model
		devs_model = yamlHandler.getDevsInstance()
		
		### launch simulation
		if devs_model:
			simulate(devs_model, duration, args.name, args.remote, args.with_progress)
		else:
			sys.stdout.write(_("ERROR: No model to simulate!\n"))
			sys.exit(1)
			