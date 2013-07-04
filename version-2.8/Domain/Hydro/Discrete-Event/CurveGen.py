# -*- coding: utf-8 -*-

"""
Name : CurveGen.py 
Brief descritpion : Curve generator for consumption
Author(s) : L. Capocchi (capocchi@univ-corse.fr), J.F. Santucci (santucci@univ-corse.fr)
Version :  1.0
Last modified : 2012.12.06
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

import os
import numpy as np

from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message

class CurveGen(DomainBehavior):
	"""
	"""

	def __init__(self, fileName = os.path.join(os.getcwd(), "water_supply.csv")):
		"""
			@water_supply : input of dam (curve on 52 weeks) for consumption
		"""
		
		DomainBehavior.__init__(self)
		
		if os.path.exists(fileName):
			### read intakes file to init attribut
			with open(fileName, 'r') as f:
				self.water_supply = np.array(map(lambda s: float(s.replace('\n','').split(' ')[-1]), f.readlines()), float)
				
		self.state = {	'status': 'ACTIVE', 
						'sigma':0.0
						}
		
	def outputFnc(self):
		self.poke(self.OPorts[0], Message([self.water_supply, 0.0, 0.0], self.timeNext))
			
	def intTransition(self):
		self.state['status'] = 'IDLE'
		self.state['sigma'] = INFINITY
		
	def timeAdvance(self): return self.state['sigma']
		
	def __str__(self): return "CurveGen"