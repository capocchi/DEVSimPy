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
import importlib

path = builtins.__dict__['DEVS_DIR_PATH_DICT'][builtins.__dict__['DEFAULT_DEVS_DIRNAME']]
d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')
BaseDEVS = importlib.import_module("DEVSKernel%s.DEVS"%d)

# ### import the DEVS module depending on the selected DEVS package in DEVSKernel directory
# for pydevs_dir in builtins.__dict__['DEVS_DIR_PATH_DICT']:
#     if pydevs_dir == builtins.__dict__['DEFAULT_DEVS_DIRNAME']:
#         path = builtins.__dict__['DEVS_DIR_PATH_DICT'][pydevs_dir]
#         ### split from DEVSKernel string and replace separator with point
#         d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')
        
# 		### for py 3.X
#         import importlib
#         BaseDEVS = importlib.import_module("DEVSKernel%s.DEVS"%d)
        
# 		### for py 2.X
#         #exec("import DEVSKernel%s.DEVS as BaseDEVS"%(d))


#    ======================================================================    #
class DomainBehavior(BaseDEVS.AtomicDEVS):
	""" Abstract DomainBehavior class.
	"""
	
	__slots__ = ('state')

	###
	def __init__(self, name:str=""):
		"""	Constructor.
		"""

		BaseDEVS.AtomicDEVS.__init__(self, name=name)

		self.state = {'status':'NOT_DEFINED', 'sigma':0.0}
		
		### if BaseDEVS AtomicDEVS class has the peek method, we have the PyDEVS simulator kernel
		### else its the PyPDEVS simulator kernel and we adapt the peek and poke method for compatibility aspects 
		if hasattr(BaseDEVS.AtomicDEVS, 'peek'):
			DomainBehavior.peek = BaseDEVS.AtomicDEVS.peek
			DomainBehavior.poke = BaseDEVS.AtomicDEVS.poke
			DomainBehavior.getMsgValue = DomainBehavior.getMsgPyDEVSValue
			DomainBehavior.getMsgTime = DomainBehavior.getMsgPyDEVSTime
			DomainBehavior.getPortId = DomainBehavior.getPortIdFromPyDEVS
		else:
			DomainBehavior.peek = DomainBehavior.peekPyPDEVS
			DomainBehavior.poke = DomainBehavior.pokePyPDEVS
			DomainBehavior.getMsgValue = DomainBehavior.getMsgPyPDEVSValue
			DomainBehavior.getMsgTime = DomainBehavior.getMsgPyPDEVSTime
			DomainBehavior.getPortId = DomainBehavior.getPortIdFromPyPDEVS

	def initPhase(self, phase:str="IDLE", sigma:float=0.0)->None:
		self.state = {'status':phase, 'sigma':sigma}

	def setSigma(self,sigma:float=0.0)->None:
		self.state['sgima'] = sigma

	def setStatus(self, phase:str)->None:
		self.state['status'] = phase

	def setState(self, s:dict)->None:
		self.state = s

	def phaseIs(self, phase:str)->bool:
		return phase == self.state['status']

	def passivate(self)->dict:
		return self.passivateIn('passive')

	def passivateIn(self, phase:str="")->dict:
		return self.holdIn(phase, sigma=INFINITY)

	def holdIn(self, phase:str="", sigma:float=0.0)->dict:
		''' "Holding in phase " + phase + " for time " + sigma
		'''
		self.state['status'] = phase
		self.state['sigma'] = sigma

		return self.state

	###
	def pokePyPDEVS(self, p, v)->dict:
		### adapted with PyPDEVS
		from .Object import Message
		if isinstance(v, Message):
			v = (v.value,v.time)
		return {p:v}

	def peekPyPDEVS(self, port, *args):
		### adapted with PyPDEVS
		inputs = args[0]
		return inputs.get(port)

	### getters
	def getPortIdFromPyDEVS(self, p):
		return p.myID

	def getPortIdFromPyPDEVS(self,p):
		if hasattr(p, 'myID'):
			return p.myID
		else:
			return p.port_id

	def getMsgPyDEVSValue(self, msg):
		return msg.value if msg else "Msg is none"		
		
	def getMsgPyPDEVSValue(self, msg):
		return msg[0] if msg else "Msg is none"

	def getMsgPyDEVSTime(self, msg):
		return msg.time	if msg else "Msg is none"
		
	def getMsgPyPDEVSTime(self, msg):
		return msg[1][0] if msg else "Msg is nore"

	def getFlatComponentSet(self):
		return {self.name:self}

	def getSigma(self)->float:
		return self.state['sigma']

	def getStatus(self)->str:
		return self.state['status']

	def getState(self)->dict:
		return self.state

	def getElapsed(self)->float:
		return self.elapsed
		
	def __str__(self)->str:
		"""
		"""
		if hasattr(self, 'bloclModel'):
			return self.blockModel.label
		else:
			return self.__class__.__name__

	def __lt__(self, other):
		return self.state['sigma'] > other.state['sigma']
		
def main():
	DB = DomainBehavior()

if __name__ == '__main__':
	main()
