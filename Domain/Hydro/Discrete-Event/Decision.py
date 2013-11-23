# -*- coding: utf-8 -*-

"""
Name : Decision.py 
Brief descritpion : 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr), SANTUCCI (santucci@univ-corse.fr)
Version :  1.0                                        
Last modified : 10/01/13
GENERAL NOTES AND REMARKS: 	
GLOBAL VARIABLES AND FUNCTIONS: 
	
"""
import sys, os, copy

from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message
  
#    ======================================================================    #
class Decision(DomainBehavior):
	""" Decision atomic model
	"""

	###
	def __init__(self, niter=100000, interval=53.0):
		"""	Constructor
		"""

		DomainBehavior.__init__(self)
		
		self.niter = niter
		self.interval = interval
		
		### control viariables must be implemented by the user
		self.control_bag = {	'figari':{'overflowing':0.0, 'discharge':0.0, 'level':0.0, 'drought':False}, 
								'ospedale':{'overflowing':0.0, 'discharge':0.0, 'level':0.0, 'drought':False}
							}
		
		# state variable declaration
		self.state = {'status':'Idle','sigma':self.interval}
	
	def extTransition(self):
		""" Transition function that implement the control rules defined bu the user.
		"""
		
		### peek messages
		for port,msg in self.peek_all():
			i = port.myID
			v = msg.value[0]
			if i == 0:
				self.control_bag['ospedale']['overflowing']+= v
			elif i == 1:
				self.control_bag['figari']['overflowing']+= v
			elif i == 2:
				self.control_bag['ospedale']['discharge']+= v
			elif i == 3:
				self.control_bag['figari']['discharge']+= v
			elif i == 4:
				self.control_bag['ospedale']['level']= v
			elif i == 5:
				self.control_bag['figari']['level']= v
			elif i == 6:
				self.control_bag['ospedale']['drought'] = True
			else:
				self.control_bag['figari']['drought'] = True
		
		self.state['sigma'] -= self.elapsed
		
	def intTransition(self):
		"""
		"""
		### there is more iterations
		if self.niter == 0:
			self.state['sigma'] = INFINITY
		else:
			self.control_bag = {	'figari':{'overflowing':0.0, 'discharge':0.0, 'level':0.0, 'drought': False},
						'ospedale':{'overflowing':0.0, 'discharge':0.0, 'level':0.0, 'drought': False}
			}
			self.state['sigma'] = self.interval
			
	###
	def outputFnc(self):
		"""
		"""
		### first decrease the number of iteration
		self.niter -= 1
		### if there is any more iteration to be performed, 
		if self.niter >= 0:
			self.poke(self.OPorts[0], Message([self.control_bag, 0.0, 0.0], self.timeNext))
			if not self.control_bag['ospedale']['drought'] and not self.control_bag['figari']['drought']:
				self.poke(self.OPorts[1], Message([self.control_bag, 0.0, 0.0], self.timeNext))
			
	####
	def timeAdvance(self): return self.state['sigma']

	###
	def __str__(self): return "Decision"
	