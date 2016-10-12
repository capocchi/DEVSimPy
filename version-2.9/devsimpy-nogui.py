#!/usr/bin/env python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# devsimpy-nogui.py --- DEVSimPy - The Python DEVS no GUI modeling and simulation software
#                     --------------------------------
#                            Copyright (c) 2014
#                              Laurent CAPOCCHI
#                        SPE - University of Corsica
#                     --------------------------------
# Version 2.9                                      last modified:  15/11/14
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# Bach version of DEVSimPy (whitout GUI)
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

### at the beginning to prevent with statement for python version <=2.5
from __future__ import with_statement

import os
import sys
import __builtin__
import json

__version__ = '2.9'

ABS_HOME_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

### specific builtin variables. (dont modify the defautls value. If you want to change it, go tot the PreferencesGUI from devsimpy interface.)
builtin_dict = {'SPLASH_PNG': os.path.join(ABS_HOME_PATH, 'splash', 'splash.png'),
				'DEVSIMPY_PNG': 'iconDEVSimPy.png',	# png file for devsimpy icon
				'HOME_PATH': ABS_HOME_PATH,
				'ICON_PATH': os.path.join(ABS_HOME_PATH, 'icons'),
				'ICON_PATH_16_16': os.path.join(ABS_HOME_PATH, 'icons', '16x16'),
				'SIMULATION_SUCCESS_SOUND_PATH': os.path.join(ABS_HOME_PATH,'sounds', 'Simulation-Success.wav'),
				'SIMULATION_ERROR_SOUND_PATH': os.path.join(ABS_HOME_PATH,'sounds', 'Simulation-Error.wav'),
				'DOMAIN_PATH': os.path.join(ABS_HOME_PATH, 'Domain'), # path of local lib directory
				'NB_OPENED_FILE': 5, # number of recent files
				'NB_HISTORY_UNDO': 5, # number of undo
				'OUT_DIR': 'out', # name of local output directory (composed by all .dat, .txt files)
				'PLUGINS_PATH': os.path.join(ABS_HOME_PATH, 'plugins'), # path of plug-ins directory
				'FONT_SIZE': 12, # Block font size
				'LOCAL_EDITOR': True, # for the use of local editor
				'LOG_FILE': os.devnull, # log file (null by default)
				'DEFAULT_SIM_STRATEGY': 'bag-based', #choose the default simulation strategy for PyDEVS
				'PYDEVS_SIM_STRATEGY_DICT' : {'original':'SimStrategy1', 'bag-based':'SimStrategy2', 'direct-coupling':'SimStrategy3'}, # list of available simulation strategy for PyDEVS package
                'PYPDEVS_SIM_STRATEGY_DICT' : {'classic':'SimStrategy4', 'distributed':'SimStrategy5', 'parallel':'SimStrategy6'}, # list of available simulation strategy for PyPDEVS package
				'HELP_PATH' : os.path.join('doc', 'html'), # path of help directory
				'NTL' : False, # No Time Limit for the simulation
				'DYNAMIC_STRUCTURE' : False, #Dynamic structure for PyPDEVS simulation
				'TRANSPARENCY' : True, # Transparancy for DetachedFrame
				'DEFAULT_PLOT_DYN_FREQ' : 100, # frequence of dynamic plot of QuickScope (to avoid overhead),
				'DEFAULT_DEVS_DIRNAME':'PyDEVS', # default DEVS Kernel directory
				'DEVS_DIR_PATH_DICT':{'PyDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyDEVS'),
									'PyPDEVS_221':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','pypdevs221' ,'src'),
									'PyPDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','old')},
				'GUI_FLAG' : True,
				'INFINITY' : float('inf')
				}

builtin_dict['GUI_FLAG'] = False

from InteractionYAML import YAMLHandler

def simulate(devs, duration, simu_name, is_remote):

	from SimulationNoGUI import makeSimulation

	if str(duration) in ('inf', 'ntl'):
		__builtin__.__dict__['NTL'] = True
		duration = 0.0

	### launch simulation
	makeSimulation(devs, duration, simu_name, is_remote, True)

# Sets the homepath variable to the directory where your application is located (sys.argv[0]).
__builtin__.__dict__.update(builtin_dict)

#-------------------------------------------------------------------
if __name__ == '__main__':

 	import gettext
 	_ = gettext.gettext

	import argparse
 	#print(sys.argv)
	parser = argparse.ArgumentParser(description="simulate a model unless other option is specified")
	# required filename
	parser.add_argument("filename", help="dsp or yaml devsimpy file")
	# optional simulation_time for simulation
	parser.add_argument("simulation_time", nargs='?', help="simulation time [inf|ntl]", default=10)
	# optional simulation_name for remote execution
	parser.add_argument("-remote", help="remote execution", action="store_true")
	parser.add_argument("-name", help="simulation name", type=str, default="simu")
	# optional kernel for simulation kernel
	parser.add_argument("-kernel", help="simulation kernel [pyDEVS|PyPDEVS]", type=str, default="pyDEVS")
	# non-simulation options
	group = parser.add_mutually_exclusive_group()
	group.add_argument("-js", "--javascript",help="generate JS file", action="store_true")
	group.add_argument("-json", help="turn the YAML/DSP file to JSON", action="store_true")
	group.add_argument("-blockslist", help="get the list of models in a master model", action="store_true")
	group.add_argument("-blockargs", help="parameters of an atomic model", type=str)
	parser.add_argument("-updateblockargs", help="new parameters", type=str, default="")
	args = parser.parse_args()

	if args.kernel:
		if 'PyPDEVS' in args.kernel:
			__builtin__.__dict__['DEFAULT_DEVS_DIRNAME'] = 'PyPDEVS_221'
			__builtin__.__dict__['DEFAULT_SIM_STRATEGY'] = 'parallel'

	filename = args.filename

	if not os.path.exists(filename):
		sys.stderr.write(_('ERROR: devsimpy file does not exist!\n'))
		sys.exit()
	else:
		yamlHandler = YAMLHandler(filename)

	if args.javascript:
		# Javascript generation
		yamlHandler.getJS()
	elif args.json:
		# turn the YAML/DSP file to JSON
		j = yamlHandler.getJSON()
		sys.stdout.write(json.dumps(j))
	elif args.blockslist:
		# get the list of models in a master model
		l = yamlHandler.getYAMLBlockModelsList()
		sys.stdout.write(json.dumps(l))
	elif args.blockargs:
		# model block parameters read or update
		label = args.blockargs
		if args.updateblockargs :
			args = json.loads(args.updateblockargs)
			new_args = yamlHandler.setYAMLBlockModelArgs(label, args)
			sys.stdout.write(json.dumps(new_args))
		else:
			args = yamlHandler.getYAMLBlockModelArgs(label)
			sys.stdout.write(json.dumps(args))

	else:
		# simulation
		duration = args.simulation_time
		if isinstance(duration, str):
			duration = float(duration)

		devs = yamlHandler.getDevsInstance()
		if devs:
			simulate(devs, duration, args.name, args.remote)

	#~ yamlHandler = YAMLHandler(filename)

	#~ if not yamlHandler.filename_is_valid:
		#~ sys.stderr.write(_('ERROR: Invalid file!\n'))
		#~ sys.exit()


 	#~ #sys.stdout.write(_("DEVSimPy - version %s\n"%__version__ ))
 	#~ nb_args = len(sys.argv)

	#~ ### First argument is filename - validity check
	#~ filename = sys.argv[1] if nb_args > 1 else None

	#~ if not filename:
		#~ sys.stderr.write(_('ERROR: Unspecified devsimpy file!\n'))
		#~ sys.exit()
	#~ elif not os.path.exists(filename):
		#~ sys.stderr.write(_('ERROR: devsimpy file does not exist!\n'))
		#~ sys.exit()

	#~ yamlHandler = YAMLHandler(filename)

	#~ if not yamlHandler.filename_is_valid:
		#~ sys.stderr.write(_('ERROR: Invalid file!\n'))
		#~ sys.exit()

	#~ if nb_args == 2:
		#~ ########################################################################
		#~ # Simulation with default simulated duration
		#~ devs = yamlHandler.getDevsInstance()
		#~ if devs :
			#~ simulate(master=devs, T = 10.0, socket_id="")

	#~ elif nb_args >= 3:
		#~ action = sys.argv[2]

		#~ if action in ('-js','-javascript'):
		#~ ########################################################################
		#~ # Javascript generation
			#~ yamlHandler.getJS()

		#~ elif action in ('-json'):
		#~ ########################################################################
		#~ # turn the YAML/DSP file to JSON

			#~ j = yamlHandler.getJSON()
			#~ sys.stdout.write(json.dumps(j))

		#~ elif action in ('-blockslist'):
		#~ ########################################################################
		#~ # get the list of models in a master model
			#~ list = yamlHandler.getYAMLBlockModelsList()
			#~ sys.stdout.write(json.dumps(list))

		#~ elif action in ('-getblockargs'):
		#~ ########################################################################
		#~ # get the parameters of an atomic model

			#~ if nb_args == 4:
				#~ label = sys.argv[3]
				#~ args = yamlHandler.getYAMLBlockModelArgs(label)
				#~ sys.stdout.write(json.dumps(args))
			#~ else:
				#~ sys.stderr.write(_('ERROR: Unspecified label for model!\n'))
				#~ sys.exit()

		#~ elif action in ('-setblockargs'):
		#~ ########################################################################
		#~ # update the parameters of a block of a model

			#~ if nb_args == 5:
			    #~ import json
			    #~ label = sys.argv[3]
			    #~ #print (sys.argv[4])
			    #~ args = json.loads(sys.argv[4])
			    #~ new_args = yamlHandler.setYAMLBlockModelArgs(label, args)
			    #~ sys.stdout.write(json.dumps(new_args))
			#~ else:
			    #~ sys.stderr.write(_("unexpected nb_args="  + str(nb_args)))
			    #~ #sys.stderr.write(_('ERROR: usage devsimpy-nogui.py dsp_or_yaml_filename -setmodelargs block_label args_as_JSON_string!\n'))
			    #~ #sys.exit()

		#~ else:
		#~ ########################################################################
		#~ # Simulation without socket communication
			#~ duration = sys.argv[2]
			#~ if nb_args == 4:
				#~ socket_id = sys.argv[3]
			#~ else:
				#~ socket_id = ""
			#~ devs = yamlHandler.getDevsInstance()
			#~ if devs :
				#~ simulate(devs, duration, socket_id)

	#~ else:
		#~ sys.stderr.write(_('ERROR: Unspecified .dsp file!\n'))
		#~ sys.stdout.write(_('USAGE: to simulate $python devsimpy-nogui.py yourfile.dsp [time=10.0|[inf|ntl]]\n'))
		#~ sys.stdout.write(_('USAGE: to generate JS file $python devsimpy-nogui.py yourfile.dsp [-js|-javascript]\n'))
		#~ sys.exit()
