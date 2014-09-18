#!/usr/bin/env python
# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# CommandLine.py ---
#                     --------------------------------
#                            Copyright (c) 2013
#                              Andre-Toussaint Luciani
#                        SPE - University of Corsica
#                     --------------------------------
# Version 3.0                                      last modified:  28/03/13
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#	This file contains command line options and argument parsing.
#
# ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
__author__ = 'luciani_at'

import os
import sys
import argparse
import __builtin__


class cleanConfigFile(argparse.Action):
	def __call__(self, parser, namespace, values, option_string=None):
		# print '%r %r %r' % (namespace, values, option_string)
		import wx
		sp = wx.StandardPaths.Get()
		config_file = os.path.join(sp.GetUserConfigDir(), '.devsimpy')
		r = raw_input('Are you sure to delete DEVSimPy config file ? (Y,N):')
		if r in ('Y', 'y', 'yes', 'Yes'):
			os.remove(config_file)
			sys.stdout.write('%s has been deleted !\n' % config_file)

		elif r in ('N', 'n', 'no', 'No'):
			pass
		else:
			pass
		sys.exit()


class clearAllPyc(argparse.Action):
	def __call__(self, parser, namespace, values, option_string=None):
		# print '%r %r %r' % (namespace, values, option_string)
		import re
		import compileall
		compileall.compile_dir('.', maxlevels=20, rx=re.compile(r'/\.svn'))
		sys.stdout.write('all pyc has been deleted !\n')
		sys.exit()


class defineLogFile(argparse.Action):
	def __call__(self, parser, namespace, values, option_string=None):
		# print '%r %r %r' % (namespace, values, option_string)
		LOG_FILE = 'log.txt'
		sys.stdout.write('Writing %s file. \n' % LOG_FILE)


class readMe(argparse.Action):
	def __call__(self, parser, namespace, values, option_string=None):
		# print '%r %r %r' % (namespace, values, option_string)
		readmeFile = 'README.md'
		f = open(readmeFile)
		try:
			for line in f:
				print line
		finally:
			f.close()
		sys.exit()


class devsimpyNoGuiWithoutTime(argparse.Action):
	def __call__(self, parser, namespace, values, option_string=None):
		# print '%r / %r / %r' % (namespace, values, option_string)

		from Core.Simulation.SimulationNoGUI import makeSimulation
		filename = str(values[0])
		time = 10.0
		
		if not os.path.exists(filename):
			sys.stderr.write('Error : .dsp not exist !\n')
			sys.exit()
		
		### launch simulation
		makeSimulation(filename, time)

		
class devsimpyNoGuiWithTime(argparse.Action):
	def __call__(self, parser, namespace, values, option_string=None):
		# print '%r / %r / %r' % (namespace, values, option_string)
		from Core.Simulation.SimulationNoGUI import makeSimulation

		filename = str(values[0])
		time = float(values[1])

		if not os.path.exists(filename):
			sys.stderr.write('Error : .dsp not exist !\n')
			sys.exit()

		### launch simulation
		makeSimulation(filename, time)
		

class devsimpyJavascript(argparse.Action):
	def __call__(self, parser, namespace, values, option_string=None):
		# print '%r %r %r' % (namespace, values, option_string)
		from Core.Simulation.SimulationNoGUI import makeJS
		### check dsp filename
		filenameJS = values[0]
		if not os.path.exists(filenameJS):
			sys.stderr.write('Error : .dsp not exist !\n')
			sys.exit()

		### launch simulation
		makeJS(filenameJS)

#
# def main(argv):
# 	parser = argparse.ArgumentParser(description="Aide à l'utilisation de DEVSimPy.")
# 	parser.add_argument('-c', nargs="?", action=cleanConfigFile, default=argparse.SUPPRESS, help='in order to delete the config file.')
# 	parser.add_argument('-m', nargs="?", action=clearAllPyc, default=argparse.SUPPRESS, help='in order to delete all files pyc.')
# 	parser.add_argument('-d', '--debug', nargs="?", action=defineLogFile, default=argparse.SUPPRESS,
# 						help='in order to define log file.')
# 	parser.add_argument('-rd', '--readme', nargs="?", action=CommandLine.readMe, default=argparse.SUPPRESS,
# 						help='in order to read the readme.')
# 	parser.add_argument('-ng', '--noguiWithoutTime', action=devsimpyNoGuiWithoutTime, dest='nogui', nargs=1,
# 						help='python devsimpy.py -ng|--nogui yourfile.dsp -> in order to start the application without a GUI.')
# 	parser.add_argument('-ngt', '--noguiWithTime', action=devsimpyNoGuiWithTime, dest='noguiTime', nargs=2,
# 						help='python devsimpy.py -ngt|--noguiWithTime yourfile.dsp 10.0 -> in order to start the application without a GUI and set the time value.',)
# 	parser.add_argument('-js', '--javascript', nargs=1, action=devsimpyJavascript, dest='fileJS', default=argparse.SUPPRESS,
# 						help='python devsimpy.py -js|--javascript yourfile.dsp -> in order to generate a file js.')
# 	parser.add_argument('--version', action='version', version='%(prog)s 3.0')
	# args = parser.parse_args()
	# print 'simple_value     =', args.simple_value
