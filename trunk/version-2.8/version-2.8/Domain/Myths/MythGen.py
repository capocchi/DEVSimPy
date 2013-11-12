# -*- coding: utf-8 -*-

"""
Name : MythGen.py 
Brief descritpion : Sinus generator atomic model 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr)
Version :  1.0                                        
Last modified : 21/03/09
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS:
"""

import os
from Domain.Myths.MythDomainBehavior import MythDomainBehavior
from Domain.Myths.Object import Myth, Message
        
#    ======================================================================    #
class MythGen(MythDomainBehavior):
	""" Sinus atomic model.
	"""

	###
	def __init__(self, fileName=""):
		"""	Constructor
		"""

		MythDomainBehavior.__init__(self)
		
		# state variable declaration
		self.state = {	'status':'ACTIVE','sigma':0}
		
		# Local copy    
		self.fileName = fileName
	
	###
  	def intTransition(self):
		"""
		"""
		# (idle during dt)
		self.state["sigma"] = INFINITY
		
	###
  	def outputFnc(self):
		"""
		"""
		f = open(self.fileName,'r')
		mythemList = map(lambda line: line.split(' '), map(lambda l: l.strip('\n'), f.readlines()))
		f.close()

		name = os.path.splitext(os.path.basename(self.fileName))[0]

		self.poke(self.OPorts[0], Message([Myth(name,"",mythemList)],self.timeNext))

	###
  	def timeAdvance(self): return self.state['sigma']

	###
	def __str__(self): return "MythGen"
