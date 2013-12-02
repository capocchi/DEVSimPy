# -*- coding: utf-8 -*-

"""
Name : Enumerate.py 
Brief descritpion : 
Author(s) : Laurent CAPOCCHI (capocchi@univ-corse.fr), SANTUCCI (santucci@univ-corse.fr)
Version :  1.0                                        
Last modified : 08/01/13
GENERAL NOTES AND REMARKS: 
	- depends on numpy package
	- the middle of trapeze for ospedal and figari consumptions is equal to the min of the resp. orgone and asinao distr.
	- week 22 to 26 in 2012 is June, week 31 to 35 in 2012 is August
	- the max of consumptio is equal to the max of corresp. intakes.
		
GLOBAL VARIABLES AND FUNCTIONS: 
	- trapeze
	
"""
import sys, os

import numpy as np

from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message
  
#    ======================================================================    #
class Enumerate(DomainBehavior):
	""" Enumerate atomic model
	"""

	###
	def __init__(self):
		"""	Constructor
		"""

		DomainBehavior.__init__(self)
		
		self.asinao = np.array([])
		self.orgone = np.array([])
		
		self.commande = None
		
		self.new_max_figari = 0.0
		self.new_middle_figari = 0.0
		self.new_base_figari = 0.0
		self.new_conso = np.array([])
		
		### ratio to manage overflowing for ospedale (turbine) and figari (pumping)
		self.ratio = 0.05
		
		self.decision = {}
		
		self.strategy = 1
		
		# state variable declaration
		self.state = {'status':'ACTIVE','sigma':INFINITY}
	
	def extTransition(self):

		### peek messages init message
		for port,msg in self.peek_all():
			i = port.myID
			v = msg.value[0]
			
			if i == 0:
				self.asinao = v
				
				### init values for ospedale
				self.middle_c1_ospedale = self.asinao.argmin()
				self.base_c1_ospedale = 5
				self.slop_l_ospedale = 5
				self.slop_r_ospedale = 10
				self.max_c1_ospedale = self.asinao.max()/2
			
				self.c1_ospedale = trapeze(self.middle_c1_ospedale, s_l = self.slop_l_ospedale, s_r = self.slop_r_ospedale, b = self.base_c1_ospedale, m = self.max_c1_ospedale)
								
				### write file
				#np.savetxt("c1_ospedale.csv", self.c1_ospedale, delimiter=" ")
				
				### the two curves must be cross
				assert(not all([s > 0 for s in np.polysub(self.asinao, self.c1_ospedale)]))
				### first resp. last value of ospedale must be bellow the first resp.the last value of asinao
				assert(self.c1_ospedale[0] < self.asinao[0] and self.c1_ospedale[-1] < self.asinao[-1])
				
				if hasattr(self, 'c1_ospedale') and hasattr(self, 'c2_figari'):
					self.conso = np.polyadd(self.c1_ospedale, self.c2_figari)
					self.new_max_figari = self.max_c2_figari
					self.new_middle_figari = self.middle_c2_figari
					self.new_base_figari = self.base_c2_figari
					self.new_conso = self.conso
					print 'New -----------------------------------'
					#print self.c2_figari
					#print self.c1_ospedale
				
					self.state['sigma'] = 0
				else:
					self.state['sigma'] = INFINITY
		
			elif i == 1:
				self.orgone = v
				
				### init values for figari
				self.middle_c2_figari = self.orgone.argmin()
				self.base_c2_figari = 5
				self.slop_l_figari = 10
				self.slop_r_figari = 5
				self.max_c2_figari = self.orgone.max()/2
				
				self.c2_figari = trapeze(self.middle_c2_figari, s_l = self.slop_l_figari, s_r = self.slop_r_figari, b = self.base_c2_figari, m = self.max_c2_figari, o=0.0)
								
				#np.savetxt("c2_figari.csv", self.c2_figari, delimiter=" ")
				
				### the two curves must be cross
				assert(not all([s > 0 for s in np.polysub(self.orgone, self.c2_figari)]))
				### first resp. last value of figari must be bellow the first resp.the last value of orgone
				assert(self.c2_figari[0] < self.orgone[0] and self.c2_figari[-1] < self.orgone[-1])
			
				if hasattr(self, 'c1_ospedale') and hasattr(self, 'c2_figari'):
					self.conso = np.polyadd(self.c1_ospedale, self.c2_figari)
					self.new_max_figari = self.max_c2_figari
					self.new_middle_figari = self.middle_c2_figari
					self.new_base_figari = self.base_c2_figari
					self.new_conso = self.conso
					print 'New -----------------------------------'
					#print self.c2_figari
					#print self.c1_ospedale
				
					self.state['sigma'] = 0
				else:
					self.state['sigma'] = INFINITY
			else:
				
				self.commande = v
				
				drough = self.commande['figari']['drought'] or self.commande['ospedale']['drought']
				
				if drough:
					
					### figari is drough ?
					if self.commande['figari']['drought']:
						
						ratio = np.random.rand()
						while(ratio > 0.95):
							ratio = np.random.rand()
							
						self.max_c2_figari -= self.max_c2_figari*ratio
						
						#if self.middle_c2_figari-1 <= 0:
							#self.middle_c2_figari -=1
							
						self.new_max_figari = self.max_c2_figari
						self.new_middle_figari = self.middle_c2_figari
						self.new_base_figari = self.base_c2_figari
						self.decision['old_gain'] = 0.0
						#self.new_conso = np.roll(np.roll(self.conso, 0), self.new_middle_figari-self.middle_c2_figari)
						self.strategy = 1
						print "drought figari" 
					
					### drough is drough ?
					else:
						ratio = np.random.rand()
						while(ratio > 0.95):
							ratio = np.random.rand()
							
						self.max_c2_figari += self.max_c2_figari*ratio
						
						#if self.middle_c2_figari+1 <= 53:
							#self.middle_c2_figari +=1
							
						self.new_max_figari = self.max_c2_figari
						self.new_middle_figari = self.middle_c2_figari
						self.new_base_figari = self.base_c2_figari
						self.decision['old_gain'] = 0.0
						#self.new_conso = np.roll(np.roll(self.conso, 0), self.new_middle_figari-self.middle_c2_figari)
							
						self.strategy = 1
						print "drought ospedal"
				else:
					
					new_turbine = self.commande['ospedale']['overflowing']
					new_pompage = self.commande['figari']['discharge']
						
					### first we choose to decrease the level of the figari consumptio curve 
					if not 'old_gain' in self.decision:	
						self.new_max_figari -= self.new_max_figari*self.ratio
						self.decision['old_gain'] = 0.0
						self.strategy = 1
					else:
						
						new_gain = abs(new_turbine - new_pompage)
						old_gain = self.decision['old_gain']
						
						if self.strategy == 1:
							### we decide to continu to descrease the consumptio of figari
							if new_gain > old_gain:
								self.new_max_figari -= self.new_max_figari*self.ratio
								print 'amélioration 1', new_gain, old_gain
								### update decision value
								self.decision['old_gain'] =  new_gain
							else:
								self.new_max_figari += self.new_max_figari*self.ratio
								print 'pas amélioration 1', new_gain, old_gain
								new_gain = self.decision['old_gain']
								old_gain = 0.0
								self.decision['old_gain'] =  0.0
								self.strategy = 4
							
						if self.strategy == 2:
							### we decide to  increase the middle of the base of the comsumption of figari
							if new_gain > old_gain:
								self.new_middle_figari +=1
								print self.new_middle_figari-self.middle_c2_figari, self.new_middle_figari
								#self.new_conso = np.roll(np.roll(self.conso, 0), self.new_middle_figari-self.middle_c2_figari)
								print 'amélioration 2', new_gain, old_gain
								### update decision value
								self.decision['old_gain'] =  new_gain
							else:
								self.new_middle_figari -=1
								print self.middle_c2_figari-self.new_middle_figari, self.new_middle_figari 
								#self.new_conso = np.roll(np.roll(self.conso, 0), -(self.middle_c2_figari-self.new_middle_figari))
								print 'pas amélioration 2', new_gain, old_gain
								new_gain = self.decision['old_gain']
								old_gain = 0.0
								self.decision['old_gain'] =  0.0
								self.strategy = 3
							
						if self.strategy == 3:
							### we decide to decrease the middle of the base of the comsumption of figari
							if new_gain > old_gain:
								self.new_middle_figari -=1
								print self.new_middle_figari-self.middle_c2_figari, self.new_middle_figari
								#self.new_conso = np.roll(np.roll(self.conso, 0), self.new_middle_figari-self.middle_c2_figari)
								print 'amélioration 3', new_gain, old_gain
								### update decision value
								self.decision['old_gain'] =  new_gain
							else:
								self.new_middle_figari +=1
								print self.middle_c2_figari-self.new_middle_figari, self.new_middle_figari 
								#self.new_conso = np.roll(np.roll(self.conso, 0), -(self.middle_c2_figari-self.new_middle_figari))
								print 'pas amélioration 3', new_gain, old_gain
								new_gain = self.decision['old_gain']
								old_gain = 0.0
								self.decision['old_gain'] =  0.0
								self.strategy = 4
								
						### change the base
						if self.strategy == 4:
							if new_gain > old_gain:
								self.new_base_figari -=2
								print 'amélioration 4', new_gain, old_gain
								### update decision value
								self.decision['old_gain'] =  new_gain
							else:
								self.new_base_figari +=2
								print 'pas amélioration 4', new_gain, old_gain
								new_gain = self.decision['old_gain']
								old_gain = 0.0
								self.decision['old_gain'] =  0.0
								self.strategy = 5
						
						if self.strategy == 5:
							if new_gain > old_gain:
								self.new_base_figari +=2
								print 'amélioration 5', new_gain, old_gain
								### update decision value
								self.decision['old_gain'] =  new_gain
							else:
								self.new_base_figari -=2
								print 'pas amélioration 5', new_gain, old_gain
								new_gain = self.decision['old_gain']
								old_gain = 0.0
								self.decision['old_gain'] =  0.0
								
								self.max_c2_figari -= self.max_c2_figari*self.ratio
								#self.middle_c2_figari -=1
								
								self.new_max_figari = self.max_c2_figari
								self.new_middle_figari = self.middle_c2_figari
								self.new_base_figari = self.base_c2_figari
								self.decision['old_gain'] = 0.0

								#self.new_conso = np.roll(np.roll(self.conso, 0), self.new_middle_figari-self.middle_c2_figari)
						
								self.strategy = 1
				
				
				### update of figari consuption curve and deduction of ospedal consumption curve 
				self.c2_figari = trapeze(
							self.new_middle_figari, 
							s_l = self.slop_l_figari, 
							s_r = self.slop_r_figari, 
							b = self.new_base_figari, 
							m = self.new_max_figari,
							o = 0.0)
				
				self.c1_ospedale = np.polysub(self.new_conso, self.c2_figari)
					
				#### if figari curve is not good, we decide to move figari curve on the left (because on the right is not good)
				#if self.new_max_figari <= 0.0 or all([s > 0 for s in np.polysub(self.orgone, self.c2_figari)]):
					#self.new_max_figari = self.max_c2_figari
					#self.new_middle_figari -=1
					#### diminution de figari
					#self.c2_figari = trapeze(
							#self.new_middle_figari, 
							#s_l = self.slop_l_figari, 
							#s_r = self.slop_r_figari, 
							#b = self.base_c2_figari, 
							#m = self.new_max_figari,
							#o = 0.0)
							
					#self.c1_ospedale = np.polysub(self.conso, self.c2_figari)
				
				self.state['sigma'] = 0
			
				#print self.c2_figari
				#print self.c1_ospedale
				
	def intTransition(self):
		self.state['sigma'] = INFINITY
		
	###
	def outputFnc(self):
		"""
		"""
				
		self.poke(self.OPorts[0], Message([self.c1_ospedale,0.0, 0.0], self.timeNext))
		self.poke(self.OPorts[1], Message([self.c2_figari,0.0, 0.0], self.timeNext))
		if 'old_gain' in self.decision and not self.commande['figari']['drought'] and not self.commande['ospedale']['drought']:
			self.poke(self.OPorts[2], Message([self.decision['old_gain'],0.0, 0.0], self.timeNext))
		self.poke(self.OPorts[3], Message([self.new_conso,0.0, 0.0], self.timeNext))
		
	###
	def timeAdvance(self): return self.state['sigma']

	###
	def __str__(self): return "Enumerate"

#######################################################
###                 <base> 
###		 ---------- max
###	       -      |     -
###  <zero_l> -     center     - <zero_r>
###  -------- <slop_l>  <slop-r> --------
###
###
#######################################################

def trapeze(c=1, b = 10, s_l = 10, s_r = 10, m = 500000, w=53, o=1000):
	"""	c = center of trapeze (1 to weeks possibility)
	b = must be pair (top of the trapeze)
	s_l = base of left slop_l
	s_r = base of left slop_r
	m = max level in m3
	w = numnber of weeks
	o = offset
	"""
	center = c 
	base = b 
	slop_l = s_l
	slop_r = s_r
	max = m
	weeks = w
	offset = o

	### test if center is good for left part
	a = center-slop_l-base/2

	if a < 0:
		zero_l = 0
		if slop_l+a < 0:
			a += slop_l
			slop_l = 0
		else:
			slop_l+=a
		
		if slop_l == 0 and a < 0:
			if base+a>0:
				base+=a
	else:
		zero_l = a 

	###################################################

	b = weeks - (zero_l+slop_l+base+slop_r)
	zero_r = b if b >=0 else 0

	interval = (zero_l, slop_l, base, slop_r, zero_r )

	### test if center is good for right part
	if sum(interval)!=weeks and zero_r==0:
		d = sum(interval) - weeks
		slop_r -= d
		if slop_r < 0:
			slop_r = 0

	interval = (zero_l, slop_l, base, slop_r, zero_r )

	if sum(interval)!=weeks and slop_r==0:
		d = sum(interval) - weeks
		base -= d
		if slop_r < 0:
			base = 0

	interval = (zero_l, slop_l, base, slop_r, zero_r )

	#########################################################
	### lets go to build x and y array and plot it

	assert(sum(interval)==weeks)

	a = np.ones(interval[0])*offset
	b = np.linspace(offset,max,interval[1])
	c = np.ones(interval[2])*max
	d = np.linspace(max,offset,interval[3])
	e = np.ones(interval[-1])*offset

	#x = np.arange(weeks)
	y = np.concatenate((a, b, c, d, e))

	return y
