# -*- coding: utf-8 -*-

"""
Name : Dam.py 
Brief descritpion : Dam atomic model 
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

class Dam(DomainBehavior):
	"""
	"""

	def __init__(self, Q0=300000.0, Qmin=10000.0, Qmax=300000.0):
		"""
			@Q0 : initial water content of the dam (m3)
			@Qmin : minimal capacity of the dam (m3)
			@Qmax : maximal capacity of the dam (m3)
		"""
		
		DomainBehavior.__init__(self)

		### local copy
		self.Q0 = Q0
		self.Qmin = Qmin
		self.Qmax = Qmax
		
		self.intakes =  np.array([])
				
		### defined by external transition
		self.water_supply = np.array([])
		
		### diff between intakes and water_supply
		self.L = []
		
		### output for water supply and turbine ports
		self.output_ws = 0.0
		self.output_turbine = 0.0
		self.output_drought = False
		self.output_command = 0.0
		
		### Q is the level of water
		self.state = {'status': 'Filling' if  self.Q0 < self.Qmax else 'Overflowing', 'sigma':INFINITY, 'QLast':Q0, 'QNext':Q0}
		
		### list of temporal index 
		self.index_dico = {0: self.state['status']}
		
	def extTransition(self):
		
		### peek messages init message
		msg3 = self.peek(self.IPorts[2])
		if msg3 is not None:
			self.intakes = msg3.value[0]
			
			self.state['sigma'] = INFINITY
			
		### peek messages init message
		msg1 = self.peek(self.IPorts[0])
		if msg1 is not None:
			self.water_supply = msg1.value[0]
			
			### diff of intakes and water_supply
			#self.L = map(lambda a,b: a-b, self.intakes, self.water_supply)
			self.L = np.polysub(self.intakes, self.water_supply)
			
			#print self.water_supply, self.intakes
			
			assert(any([v < 0 for v in self.L]))
			
			self.output_ws = 0.0
			self.output_turbine = 0.0
			self.output_drought = False
			self.output_command = 0.0
			self.state = {'status': 'Filling' if  self.Q0 < self.Qmax else 'Overflowing', 'sigma':INFINITY, 'QLast':self.Q0, 'QNext':self.Q0}
			self.index_dico = {0: self.state['status']}
			
			### t1 for winter to summer and t2 for summer to winter
			
			n = filter(lambda a: a<=0, self.L)
			self.t1 = list(self.L).index(n[0])
			self.t2 = list(self.L).index(n[-1])
			
			### simulation time for experimental frame management
			self.t = 0.0
			
			self.ChangeState()
		
		### peek command message
		msg2 = self.peek(self.IPorts[1])
		if msg2 is not None:
			
			### target
			Qt = msg2.value[0]
			
			#time = msg2.time%len(self.L)
			time = (self.t+self.elapsed)%len(self.L)
			
			sigma_old = int(time)
			
			self.output_command = 0.0
			
			if self.state['status'] == 'Filling':
			
				### if possible is below taget
				if Qt != 0.0:		
					
					### Qt negatif
					if Qt < 0.0:
						
						### clacul de la quantité dispo
						#print "A", self.timeLast, self.state['sigma']
						
						### Qp possible
						if sigma_old <= self.t1:
							Qp = sum(self.L[sigma_old:self.t1])
						elif sigma_old >= self.t2:
							Qp = sum(self.L[self.t2:sigma_old])
						else:
							Qp = 0.0
							
						### test secheresse
						if abs(Qt) > Qp:
							self.output_drought = True
							sigma = 0.0
							
					### Qt positif
					else:
						### test débordement
						#if Qp+self.state['QNext']+Qt > self.Qmax:
						pass
							
					if not self.output_drought:
						#print self.state['QNext'], self.state['QLast']
						a = int(time-self.elapsed)
						b = int(time)
						
						### give command for dam connexion
						if Qt > 0.0:
							if self.state['QNext'] < self.Qmax:
								if self.state['QLast'] + Qt > self.Qmax:
									self.output_command = -(self.Qmax - self.state['QLast'])
								else:
									self.output_command = - Qt
							else:
								self.output_command = 0.0
								Qt = 0.0
						else:
							self.output_command = 0.0
							
						self.state['QNext'] = self.state['QNext']+ sum(self.L[a:b]) + Qt
						self.state['QLast'] = self.state['QNext']
							
						self.output_ws = sum(self.water_supply[a:b])
						sigma = 0.0
							
					#print 'avant',self.index_dico
					key = int(time)
					val = self.state['status']
					del self.index_dico[max(self.index_dico.keys())]
					self.index_dico.update({key:val})
					#print 'apres', self.index_dico

				else:
					sigma = sigma_old - int(self.elapsed)
					
			else:
				
				### if possible is below taget
				if Qt != 0.0:			
					#print self.state['QNext'], self.state['QLast']
					a = int(time-self.elapsed)
					b = int(time)
				
					### give command for dam connexion
					if Qt > 0.0:
						if self.state['QNext'] < self.Qmax:
							if self.state['QLast'] + Qt > self.Qmax:
								self.output_command = -(self.Qmax - self.state['QLast'])
							else:
								self.output_command = - Qt
						else:
							self.output_command = 0.0
							Qt = 0.0
					else:
						self.output_command = 0.0
							
					self.state['QNext'] = self.state['QNext']+ sum(self.L[a:b]) + Qt
					self.state['QLast'] = self.state['QNext']
					self.output_ws = sum(self.water_supply[a:b])
					sigma = 0.0
						
					#print 'avant',self.index_dico, a, b
					key = int(time)
					val = self.state['status']
					del self.index_dico[max(self.index_dico.keys())]
					self.index_dico.update({key:val})
					#print 'apres', self.index_dico
					
				else:
					sigma = sigma_old - int(self.elapsed)
			 
			#print "sigma_old- 1------------------>", self.state['sigma']
			self.state['sigma'] = sigma
			
	def ChangeState(self): 
		
		### index begin from the utilmate date
		index = max(self.index_dico.keys())
		
		#print index
		self.t = index
		
		### status update
		if self.output_drought:
			#self.output_drought = False
			self.state['status'] = 'Drought'
			
		elif self.state['QNext'] < self.Qmax and self.state['QNext'] >= self.Qmin:
			self.state['status'] = 'Filling'
		elif self.state['QNext'] < self.Qmin:
			self.state['status'] = 'Drought'
		else:
			
			if self.water_supply != []:
				d = self.intakes[index] - self.water_supply[index]
				if d > 0.0:
					self.state['status'] = 'Overflowing'
				else:
					self.state['status'] = 'Release'
		
		### sigma update
		if self.state['status'] == 'Filling':
			r = self.L[index]
			#print "Filling", index, self.state['QLast'],self.state['QNext']
			
			while (self.state['QNext']+r < self.Qmax):
				try:
					index += 1
					r += self.L[index]
				except IndexError:
					r += self.L[index-1]
					index -= 1
					break	
				
				### check drought
				if self.state['QLast']+r < self.Qmin:
					self.output_drought = True
					#self.state['status'] = 'Drought'
					break
			
			self.debugger("Filling %d %d"%(index, r))
			
			#print "Filling", index, r
		elif self.state['status'] == 'Overflowing':
			r = self.L[index]
			#print "Overflowing", index, self.state['QLast'],self.state['QNext']
			while (r > 0.0):
				try:
					index += 1
					r = self.L[index]
				except IndexError:
					r = self.L[index-1]
					index -= 1
					break	
			#print "Overflowing", index, r		
		elif self.state['status'] == 'Release':
			r = self.L[index]
			#print "Release", index, self.state['QLast'],self.state['QNext']
			while (self.state['QLast']+r > self.Qmin):
				if self.L[index] > 0.0:
					break
				#print index, self.state['QLast']+r
				try:
					index += 1
					r += self.L[index]
				except IndexError:
					r += self.L[index-1]
					index -= 1
					break	
				
				### check drought
				if self.state['QLast']+r < self.Qmin:
					self.output_drought = True
					#self.state['status'] = 'Drought'
					break
				### overflowing
				elif self.state['QNext']+r > self.Qmax:
					break
				
	
			self.debugger("Release %d %d"%(index, r))
			
		### update dico with new status
		self.index_dico.update({index:self.state['status']})
		self.debugger(self.index_dico)
		### interval between changing state 
		l = self.index_dico.keys()
		l.sort()
		b = l[-1]
		try:
			a = l[-2]
		except IndexError:
			a = b
		
		### test for over the limite
		#if b+1 < len(self.L):
		
		#print a,b, self.L[a:b], self.state
		### update output variables
		self.output_ws = 0.0
		self.output_turbine = 0.0
		if self.state['status'] == 'Filling':
			if not self.output_drought:
				self.output_ws = sum(self.water_supply[a:b])
				t = self.state['QLast'] + r - self.Qmax
				self.output_turbine = t if t > 0.0 else 0.0
			else:
				#self.state['status'] = 'Drought'
				self.output_ws = 0.0
				self.output_turbine = 0.0
			
			if self.state['QLast'] + r >= self.Qmax:
				self.state['QLast'] = self.state['QNext']
				self.state['QNext'] = self.Qmax
			elif self.state['QLast'] + r < 0.0:
				self.state['QLast'] = self.state['QNext']
				self.state['QNext'] = self.Qmin
			else:
				self.state['QLast'] = self.state['QNext']
				self.state['QNext'] = self.state['QLast'] + r
				
			#self.state['sigma'] = abs(b-a)
			
		elif self.state['status'] == 'Overflowing':
			self.output_ws = sum(self.water_supply[a:b])
			self.output_turbine = sum(self.L[a:b])
			#self.debugger(self.state['QNext'])
			#self.state['sigma'] = abs(b-a)

		elif self.state['status'] == 'Release':
			self.output_ws = sum(self.water_supply[a:b])
			self.output_turbine = 0.0
			
			if self.state['QLast'] + r < self.Qmin:
				self.state['QLast'] = self.state['QNext']
				self.state['QNext'] = self.Qmin
			else:
				self.state['QLast'] = self.state['QNext']
				### plafonnement
				add = self.state['QLast'] + r
				self.state['QNext'] = add if add < self.Qmax else self.Qmax
			
			#self.state['sigma'] = abs(b-a)
			#else:
				#self.state['sigma'] = INFINITY
		
		### update of sigma
		### test for over the limite
		if b+1 < len(self.L):
			if self.state['status'] == 'Drought':
				self.state['sigma'] = INFINITY
			else:
				self.state['sigma'] = abs(b-a)
		else:
			if self.state['status'] == 'Release':
				self.state['sigma'] = abs(b-a)
			else:
				#self.debugger(self.index_dico)
				self.state['sigma'] = INFINITY
		
	def outputFnc(self):
		#self.debugger(self.index_dico)
		if self.output_turbine != 0.0: 
			self.poke(self.OPorts[0], Message([self.output_turbine, 0.0, 0.0], self.timeNext))
		if self.output_ws != 0.0: 
			self.poke(self.OPorts[1], Message([self.output_ws, 0.0, 0.0], self.timeNext))
		if self.output_drought:
			self.poke(self.OPorts[2], Message([self.output_drought, 0.0, 0.0], self.timeNext))
		
		self.poke(self.OPorts[3], Message([self.state['QNext'], 0.0, 0.0], self.timeNext))
		
		if self.output_command != 0.0:
			self.poke(self.OPorts[4], Message([self.output_command, 0.0, 0.0], self.timeNext))
		
	def intTransition(self):
		self.ChangeState()
		
	#def finish(self, msg):
		#self.debugger(self.index_dico)
		
	def timeAdvance(self): return self.state['sigma']
		
	def __str__(self): return "Dam"