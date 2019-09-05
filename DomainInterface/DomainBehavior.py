# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# DomainBehavior.py --- Domain Behavior virtual class
#                     --------------------------------
#                        Copyright (c) 2009
#                       Laurent CAPOCCHI
#                      University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 14/07/09
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
#  GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import builtins

### just for individual test
if __name__ == '__main__':
	import os
	import sys

	builtins.__dict__['DEFAULT_DEVS_DIRNAME'] = "PyDEVS"
	builtins.__dict__['DEVS_DIR_PATH_DICT'] = {\
	'PyDEVS':os.path.join(os.pardir,'DEVSKernel','PyDEVS'),\
	'PyPDEVS':os.path.join(os.pardir,'DEVSKernel','PyPDEVS')}

    ### permit correct import (based on from instruction) in PyPDEVS directory (logger, util...) when this module executed (main)
	d = sys.path.append(os.pardir)
	if d not in sys.path:
		sys.path.append(d)

import re
import os

### import the DEVS module depending on the selected DEVS package in DEVSKernel directory
for pydevs_dir in builtins.__dict__['DEVS_DIR_PATH_DICT']:
    if pydevs_dir == builtins.__dict__['DEFAULT_DEVS_DIRNAME']:
        path = builtins.__dict__['DEVS_DIR_PATH_DICT'][pydevs_dir]
        ### split from DEVSKernel string and replace separator with point
        d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')
        exec("import DEVSKernel%s.DEVS as BaseDEVS"%(d))

#    ======================================================================    #
class DomainBehavior(BaseDEVS.AtomicDEVS):
	""" Abstract DomainBehavior class.
	"""

	###
	def __init__(self, name=""):
		"""	Constructor.
		"""

		BaseDEVS.AtomicDEVS.__init__(self, name=name)

		### if BaseDEVS AtomicDEVS class has the peek method, we have the PyDEVS simulator kernel
		### else its the PyPDEVS simulator kernel and we adapt the peek and poke method for compatibility aspects 
		if hasattr(BaseDEVS.AtomicDEVS, 'peek'):
			DomainBehavior.peek = BaseDEVS.AtomicDEVS.peek
			DomainBehavior.poke = BaseDEVS.AtomicDEVS.poke
			DomainBehavior.getMsgValue = DomainBehavior.getMsgPyDEVSValue
			DomainBehavior.getPortId = DomainBehavior.getPortIdFromPyDEVS
		else: 
			DomainBehavior.peek = DomainBehavior.peekPyPDEVS
			DomainBehavior.poke = DomainBehavior.pokePyPDEVS
			DomainBehavior.getMsgValue = DomainBehavior.getMsgPyPDEVSValue
			DomainBehavior.getPortId = DomainBehavior.getPortIdFromPyPDEVS

	def initPhase(self, phase="IDLE", sigma=0.0):
		self.state = {'status':phase, 'sigma':sigma}

	def phaseIs(self, phase):
		return phase == self.state['status']

	def passivate(self):
		self.passivateIn('passive')

	def passivateIn(self, phase=""):
		self.holdIn(phase, sigma=INFINITY)

	def holdIn(self, phase="", sigma=0.0):
		''' "Holding in phase " + phase + " for time " + sigma
		'''
		self.state['status'] = phase
		self.state['sigma'] = sigma

	###
	def pokePyPDEVS(self, p, v):
		### adapted with PyPDEVS
		from .Object import Message
		if isinstance(v, Message):
			v = (v.value,v.time)
		return {p:v}

	def peekPyPDEVS(self, port, args):
		### adapted with PyPDEVS
		inputs = args[0]
		return inputs.get(port)

	def getPortIdFromPyDEVS(self, p):
		return p.myID

	def getPortIdFromPyPDEVS(self,p):
		return p.port_id

	def getMsgPyDEVSValue(self, msg):
		return msg.value					
		
	def getMsgPyPDEVSValue(self, msg):
		return msg[0]

	def getFlatComponentSet (self):
		return {self.name : self}

	def getSigma(self):
		return self.state['sigma']

	def getStatus(self):
		return self.state['status']

	def getState(self):
		return self.state
		
	def __str__(self):
		"""
		"""
		if hasattr(self, 'bloclModel'):
			return self.blockModel.label
		else:
			return self.__class__.__name__

def main():
	DB = DomainBehavior()

if __name__ == '__main__':
	main()
