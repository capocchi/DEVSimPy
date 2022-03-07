#!/usr/bin/env python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# devsimpy-nogui.py --- DEVSimPy - The Python DEVS no GUI modeling and simulation software
#                     --------------------------------
#                            Copyright (c) 2019
#                              Laurent CAPOCCHI
#                        SPE - University of Corsica
#                     --------------------------------
# Version 4                                      last modified:  07/03/22
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
# Bach version of DEVSimPy (whitout GUI)
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import os
import sys
import builtins
import json
import pathlib
import zipfile

from InteractionYAML import YAMLHandler

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

__version__ = '4.0'

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
                'PYPDEVS_SIM_STRATEGY_DICT' : {'classic':'SimStrategy4', 'parallel':'SimStrategy5'}, # list of available simulation strategy for PyPDEVS package
				'PYPDEVS_221_SIM_STRATEGY_DICT' : {'classic':'SimStrategy4', 'parallel':'SimStrategy5'}, # list of available simulation strategy for PyPDEVS package
				'HELP_PATH' : os.path.join('doc', 'html'), # path of help directory
				'NTL' : False, # No Time Limit for the simulation
				'DYNAMIC_STRUCTURE' : False, #Dynamic structure for PyPDEVS simulation
				'REAL_TIME': False, ### PyPDEVS threaded real time simulation
				'VERBOSE':False,
				'TRANSPARENCY' : True, # Transparancy for DetachedFrame
				'DEFAULT_PLOT_DYN_FREQ' : 100, # frequence of dynamic plot of QuickScope (to avoid overhead),
				'DEFAULT_DEVS_DIRNAME':'PyDEVS', # default DEVS Kernel directory
				'DEVS_DIR_PATH_DICT':{'PyDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyDEVS'),
									'PyPDEVS_221':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','pypdevs221' ,'src'),
									'PyPDEVS':os.path.join(ABS_HOME_PATH,'DEVSKernel','PyPDEVS','old')},
				'GUI_FLAG' : False,
				'INFINITY' : float('inf')
				}

# Sets the homepath variable to the directory where your application is located (sys.argv[0]).
builtins.__dict__.update(builtin_dict)

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

def retrieve_file_paths(dirName:str):
	""" Function to return all file paths of the particular directory

	Args:
		dirName (str): Name of the directory

	Returns:
		_type_: list of file paths
	"""
	filePaths = []

	# Read all directory, subdirectories and file lists
	for root, directories, files in os.walk(dirName):
		for filename in files:
		# Create the full filepath by using os module.
			filePath = os.path.join(root, filename)
			filePaths.append(filePath)
			
	# return all paths
	return filePaths

def devsimpy_nogui_package_build(yaml:str="", outfn:str="devsimpy-nogui-pkg.zip")->None:
	""" Generates the zip file with all files needed to execute the devsimpy-nogui script

		Args:
			yaml (str): yaml file to zip (optional)
			outfn (str): zip file to export all files
	"""

	### list of files to zip
	filenames = ["Components.py", "Container.py", "Decorators.py","devsimpy-nogui.py","DSV.py", "InteractionSocket.py","InteractionYAML.py",
				"Join.py","NetManager.py","PluginManager.py","SimulationNoGUI.py","SpreadSheet.py","Utilities.py","XMLModule.py","ZipManager.py"]

	### list of dir to zip
	dirnames = map(pathlib.Path,["DEVSKernel/","Domain/", "DomainInterface/","Mixins/","Patterns/"])

	yaml_exist = yaml.endswith('.yaml') and os.path.exists(yaml)
	
	if yaml != "" and not yaml_exist:
		return False
  
	### TODO: if yaml is passed from function param, Domain is pruned in order to select only the lib used by the model
 
	with zipfile.ZipFile(outfn, mode="w") as archive:
		
  		### add yaml file if passed 
		if yaml != "":
			path = os.path.abspath(yaml)
			archive.write(path, os.path.basename(path))

		### add all dependencies python files needed to execute devsimpy-nogui
		for filename in filenames:
			archive.write(filename)
			
		### add all dependancies (directories) needed to execute devsimpy-nogui
		for dirname in dirnames:
      
			# Call the function to retrieve all files and folders of the assigned directory
			filePaths = retrieve_file_paths(dirname)
			
			for file in filePaths:
				archive.write(file)
 
	return True

def simulate(devs, duration, simu_name, is_remote):
	"""Simulate the devs model during a specific duration.

	Args:
		devs (_type_): _description_
		duration (_type_): _description_
		simu_name (_type_): _description_
		is_remote (bool): _description_
	"""

	from SimulationNoGUI import makeSimulation

	if str(duration) in ('inf', 'ntl'):
		builtins.__dict__['NTL'] = True
		duration = 0.0

	### launch simulation
	makeSimulation(devs, duration, simu_name, is_remote, True)

#-------------------------------------------------------------------
if __name__ == '__main__':

	import gettext
	_ = gettext.gettext

	import argparse
 	
	parser = argparse.ArgumentParser(description=_("Simulate a model unless other option is specified"))
	# required filename
	parser.add_argument("filename", help=_("dsp or yaml devsimpy file only"))
	# optional simulation_time for simulation
	parser.add_argument("simulation_time", nargs='?', help=_("Simulation time [inf|ntl]"), default=10)
	# optional simulation_name for remote execution
	parser.add_argument("-remote", help=_("Remote execution"), action="store_true")
	parser.add_argument("-name", help=_("Simulation name"), type=str, default="simu")
	# optional kernel for simulation kernel
	parser.add_argument("-kernel", help=_("Simulation kernel [pyDEVS|PyPDEVS]"), type=str, default="pyDEVS")
	# optional real time 
	parser.add_argument("-rt", help=_("Real time simulation (only for PyPDEVS)"), action="store_true")
 
	# non-simulation options
	group = parser.add_mutually_exclusive_group()
	group.add_argument("-js", "--javascript",help=_("Generate JS file"), action="store_true")
	group.add_argument("-json", help=_("Turn the YAML/DSP file to JSON"), action="store_true")
	group.add_argument("-blockslist", help=_("Get the list of models in a master model"), action="store_true")
	group.add_argument("-blockargs", help=_("Parameters of an atomic model (ex. -blockargs <label of block>)"), type=str)
	parser.add_argument("-updateblockargs", help=_("Update parameters (ex. -blockargs <label of block> -updateblockargs <'''{'<key>':<val>}'''>"), type=str, default="")
	parser.add_argument("-zip", help=_("Export the devsimpy-nogui files into a filename file"), action="store_true")
 
	args = parser.parse_args()

	if args.kernel:
		if 'PyPDEVS' in args.kernel:
			builtins.__dict__['DEFAULT_DEVS_DIRNAME'] = 'PyPDEVS_221'
			builtins.__dict__['DEFAULT_SIM_STRATEGY'] = 'parallel'

			### Real time only for PyPDEVS...
			builtins.__dict__['REAL_TIME'] = args.rt

	filename = args.filename

	if not args.zip:
		
		if not os.path.exists(filename):
			sys.stderr.write(_('ERROR: devsimpy file does not exist!\n'))
			sys.exit()
		else:
			yamlHandler = YAMLHandler(filename)
  
			if not yamlHandler.filename_is_valid:
				sys.stderr.write(_('ERROR: Invalid file!\n'))
				sys.exit()

	if args.zip:
		# zip exportation
		if filename.endswith('.zip'):
			devsimpy_nogui_package_build(outfn=filename)
		else:
			sys.stderr.write(_('ERROR: Invalid file type (must be zip file)!\n'))
			sys.exit()
	elif args.javascript:
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
		if args.updateblockargs:
			# model block is updated 
			args = json.loads(args.updateblockargs)
			if isinstance(args,str):
				args = eval(args)
			new_args = yamlHandler.setYAMLBlockModelArgs(label, args)
			sys.stdout.write(json.dumps(new_args))
		else:
			args = yamlHandler.getYAMLBlockModelArgs(label)
			sys.stdout.write(json.dumps(args))

	else:
		# simulation
		duration = args.simulation_time
		if not isinstance(duration, str):
			duration = float(duration)

		devs = yamlHandler.getDevsInstance()
		if devs:
			simulate(devs, duration, args.name, args.remote)

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
