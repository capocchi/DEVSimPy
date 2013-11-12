# -*- coding: utf-8 -*-

"""
Name : Integrator3.py
Brief description : Atomic Model for integration function
Authors : Laurent CAPOCCHI
Version : 1.0
Last modified : 2/10/11
GENERAL NOTES AND REMARKS: le deuxieme port permet l'initialisation.
En mode standart, il suffit d'utiliser un ConstGen avec Xo en sortie. Pour la mise à jour il suffit de connecter le second port au modele de mise à jour.
GLOBAL VARIABLES AND FUNCTIONS
"""

from DomainInterface.DomainBehavior import DomainBehavior
from math import fabs, sqrt, acos, cos, pow

pidiv3=1.047197551

class Integrator3(DomainBehavior):
	""" Atomic model for QSS integration function.
	"""

	###
	def __init__(self, m=('QSS3','QSS2','QSS1'), dQ=0.01):
		"""	Constructor.
		
			@param m : QSS methode choise
			@param dQ : quantification level
		"""

		DomainBehavior.__init__(self)

		# State variables
		self.state = {	'status': 'IDLE', 'sigma': INFINITY}

		#local copy
		self.m = m[0]
		self.dQ = dQ
	
		self.u = 0.0
		self.mu = 0.0
		self.mq = 0.0
		self.pq = 0.0
		self.pu = 0.0

		# output message
		self.msg = None

	###
	def extTransition(self):

		# recuperation du message sur le port d'entre
		self.msg = self.peek(self.IPorts[0])

		### intercept init (or re-init) message
		try:
			self.msg_init = self.peek(self.IPorts[1])
		except IndexError:
			pass
		else:
			if self.msg_init is not None:
				self.x = self.msg_init.value[0]
				self.q = self.x
	
				self.u = 0.0
				self.mu = 0.0
				self.mq = 0.0
				self.pq = 0.0
				self.pu = 0.0
				self.state['sigma']=0
				
		e2 = self.elapsed*self.elapsed
		e3 = e2*self.elapsed
			
		## liste stockant les valeurs d'entree portees par le message
		try:
			Aux = self.msg.value
		except AttributeError:
			Aux = [0.0,0.0,0.0]
			
		if(self.m == "QSS"):
				self.x+=self.elapsed*self.u
				self.u = Aux[0]
				if (self.state['sigma'] != 0):
					
					#self.state['sigma'] = calc1(self.x, self.u, self.q, self.dQ, INFINITY)
					
					if(self.u == 0):
						self.state['sigma']=INFINITY
					elif(self.u > 0):
						self.state['sigma']=(self.q+self.dQ-self.x)/self.u
					else:
						self.state['sigma']=(self.q-self.dQ-self.x)/self.u
						
		elif(self.m == "QSS2"):
			
			self.x += self.u*self.elapsed+self.mu/2*e2
			self.u = Aux[0]
			self.mu = Aux[1]
			
			if(self.state['sigma'] != 0):
				self.q += self.mq*self.elapsed
	
				a=self.mu/2.0
				b=self.u-self.mq
				c=self.x-self.q+self.dQ
				# changement d'etat
				self.state['sigma'] = INFINITY
				
				if(a==0):
					if(b!=0):
						s=-c/b
						if(s>0):
							# changement d'etat
							self.state['sigma'] = s
						c=self.x-self.q-self.dQ
						s=-c/b
						if ((s>0) and (s<self.state['sigma'])):
							# changement d'etat
							self.state['sigma'] = s
				else:
					if (b*b-4*a*c) > 0:
						s=(-b+sqrt(b*b-4*a*c))/2/a
						if (s>0):
							# changement d'�tat
							self.state['sigma']=s
						s=(-b-sqrt(b*b-4*a*c))/2/a
						if ((s>0) and (s<self.state['sigma'])):
							# changement d'etat
							self.state['sigma']=s
					
					c=self.x-self.q-self.dQ
					if (b*b-4*a*c) > 0:	
						s=(-b+sqrt(b*b-4*a*c))/2/a
						if ((s>0) and (s<self.state['sigma'])):
							# changement d'etat
							self.state['sigma']=s
						s=(-b-sqrt(b*b-4*a*c))/2/a
						if ((s>0) and (s<self.state['sigma'])):
							# changement d'�tat
							self.state['sigma']=s
							
				if abs(self.x-self.q)>self.dQ:
					# changement d'etat
					self.state['sigma']=0
						
		else:
			
			self.x+=self.u*self.elapsed+(self.mu*e2)/2+(self.pu*e3)/3
			self.u=Aux[0]
			self.mu=Aux[1]
			self.pu=Aux[2]
			
			if(self.state['sigma'] != 0):
				
				self.q+=self.mq*self.elapsed+self.pq*e2
				self.mq+=2*self.pq*self.elapsed
				
				a=self.mu/2-self.pq
				b=self.u-self.mq
				c=self.x-self.q-self.dQ

				if(self.pu!=0):
					
					a=3*a/self.pu
					b=3*b/self.pu
					c=3*c/self.pu
					v=b-(a*a/3)
					w=c-(b*a/3)+(2*a*a*a/27)
					i1=-w/2
					i2=(i1*i1)+(v*v*v/27)
					
					if(i2>0):
						i2=sqrt(i2)
						A=i1+i2
						B=i1-i2
						if(A>0):
							A=pow(A,1.0/3)
						else:
							A=-pow(fabs(A),1.0/3)
						if(B>0):
							B=pow(B,1.0/3)
						else:
							B=-pow(fabs(B),1.0/3)	
							
						s=A+B-(a/3)
						if(s<0): s=INFINITY
						
					elif(i2==0):
						A=i1
						if(A>0):
							A=pow(A,1.0/3)
						else:
							A=-pow(fabs(A),1.0/3)
						x1=2*A-(a/3)
						x2=-(A+(a/3))
						if(x1<0):
							if(x2<0):
								s=INFINITY
							else:
								s=x2
						elif(x2<0) or (x1<x2):
							s=x1
						else:
							s=x2
					else:
						arg=(w*sqrt(27/-v))/(2*v)
						arg=acos(arg)/3.0

						#try:
							#arg=acos(arg)/3.0
						#except ValueError:
							#if (arg >= 1.0):
								#arg=0
							#elif (arg <= -1.0):
								#arg=pidiv3
							#else:
								#print "ERROR"
								#import sys
								#sys.exit(1)
						y1=2*sqrt(-v/3)
						y2=-y1*cos(pidiv3-arg)-(a/3)
						y3=-y1*cos(pidiv3+arg)-(a/3)
						y1=y1*cos(arg)-(a/3)
						if(y1<0):
							s=INFINITY
						elif(y3<0):
							s=y1
						elif(y2<0):
							s=y3
						else:
							s=y2
							
					c+=(6*self.dQ)/self.pu
					w=c-(b*a/3)+(2*a*a*a/27)
					i1=-w/2
					i2=(i1*i1)+(v*v*v/27)
					
					if(i2>0):
						
						i2=sqrt(i2)
						A=i1+i2
						B=i1-i2
						if(A>0):
							A=pow(A,1.0/3)
						else:
							A=-pow(fabs(A),1.0/3)
						if(B>0):
							A=pow(B,1.0/3)
						else:
							B=-pow(fabs(B),1.0/3)
						
						self.state['sigma']=A+B-(a/3)
						
						if (s<self.state['sigma']) or (self.state['sigma']<0):
							self.state['sigma']=s
							
					elif(i2==0):
						A=i1
						if(A>0):
							A=pow(A,1.0/3)
						else:
							A=-pow(fabs(A),1.0/3)
						x1=(2*A)-(a/3)
						x2=-(A+(a/3))
						if(x1<0):
							if(x2<0):
								self.state['sigma']=INFINITY
							else:
								self.state['sigma']=x2
						
						elif(x2<0) or (x1<x2):
								self.state['sigma']=x1
						else:
								self.state['sigma']=x2
								
						if (s<self.state['sigma']):
							self.state['sigma'] = s
				
					else:
						arg=(w*sqrt(27/-v))/(2*v)
						arg=acos(arg)/3.0

						#try:
							#arg=acos(arg)/3.0
						#except ValueError:
							#if (arg >= 1.0):
								#arg=0.0
							#elif (arg <= -1.0):
								#arg=pidiv3
							#else:
								#print "ERROR"
								#import sys
								#sys.exit(1)
						y1=2*sqrt(-v/3)
						y2=-y1*cos(pidiv3-arg)-(a/3)
						y3=-y1*cos(pidiv3+arg)-(a/3)
						y1=y1*cos(arg)-(a/3)
						if(y1<0):
							s=INFINITY
						elif(y3<0):
							s=y1
						elif(y2<0):
							s=y3
						else:
							s=y2			
						if (s<self.state['sigma']):
							self.state['sigma'] = s
				else:
					if(a!=0):
						x1=(b*b)-(4*a*c)
						if(x1<0):
							s=INFINITY
						else:
							x1=sqrt(x1)
							x2=(-b-x1)/(2*a)
							x1=(-b+x1)/(2*a)
							
							if(x1<0):
								if(x2<0):
									s=INFINITY
								else:
									s=x2
							elif(x2<0) or (x1<x2):
								s=x1
							else:
								s=x2
									
						c+=2*self.dQ
						x1=(b*b)-(4*a*c)
						if(x1<0):
							self.state['sigma']=INFINITY
						else:
							x1=sqrt(x1)
							x2=(-b-x1)/(2*a)
							x1=(-b+x1)/(2*a)
							if(x1<0):
								if(x2<0):
									self.state['sigma']=INFINITY
								else:
									self.state['sigma']=x2
							elif(x2<0) or (x1<x2):
								self.state['sigma']=x1
							else:
								self.state['sigma']=x2
								
						if (s<self.state['sigma']):	self.state['sigma']=s
						
					elif(b!=0):
						x1=-c/b
						x2=x1-2*(self.dQ/b)
						if(x1<0):
							x1=INFINITY
						if (x2<0):
							x2=INFINITY
						if(x1<x2):
							self.state['sigma']=x1
						else:
							self.state['sigma']=x2
							
				if fabs(self.x-self.q)>self.dQ: self.state['sigma']=0				
	###
  	def intTransition(self):

		if (self.m == "QSS"):
			self.x+=self.state['sigma']*self.u
			self.q=self.x
			if(self.u==0):
				self.state["status"] = 'IDLE'
				self.state["sigma"] = INFINITY
			else:
				self.state["status"] = 'IDLE'
				self.state["sigma"] = self.dQ/fabs(self.u)

		elif(self.m == "QSS2"):
			self.x+=self.u*self.state['sigma']+(self.mu/2)*self.state['sigma']*self.state['sigma']
			self.q=self.x
			self.u+=self.mu*self.state['sigma']
			self.mq = self.u
			if(self.mu==0):
				self.state["status"] = 'IDLE'
				self.state["sigma"] = INFINITY
			else:
				self.state["status"] = 'IDLE'
				self.state["sigma"] = sqrt(2*self.dQ/fabs(self.mu))
		else:
			self.x+=(self.u*self.state['sigma'])+((self.mu*pow(self.state['sigma'],2))/2) + ((self.pu*pow(self.state['sigma'],3))/3)
			self.q=self.x
			self.u+=(self.mu*self.state['sigma']) + (self.pu*pow(self.state['sigma'],2))
			self.mq = self.u
			self.mu+=2*self.pu*self.state['sigma']
			self.pq=self.mu/2
			if(self.pu==0):
				self.state["status"] = 'IDLE'
				self.state["sigma"] = INFINITY

			else:
				self.state["status"] = 'IDLE'
				self.state["sigma"] = pow(fabs(3*self.dQ/self.pu),1/3)
	###
  	def outputFnc(self):

		assert(self.msg != None or self.msg_init != None)

		self.msg = self.msg or self.msg_init
		
		if(self.m=="QSS"):
			if(self.u==0):
				val=[self.q,0,0]
			else:
				val=[self.q+self.dQ*self.u/fabs(self.u), 0.0, 0.0]

		elif(self.m == "QSS2"):
			val=[self.x+self.u*self.state['sigma']+self.mu*self.state['sigma']*self.state['sigma']/2, self.u+self.mu*self.state['sigma'], 0.0]

		else:
			val=[self.x+self.u*self.state['sigma']+(self.mu*pow(self.state['sigma'],2))/2.0 + (self.pu*pow(self.state['sigma'],3))/3.0, self.u+self.mu*self.state['sigma']+self.pu*pow(self.state['sigma'],2), self.mu/2.0 + self.pu*self.state['sigma']]

		self.msg.value = val
		self.msg.time = self.timeNext
		
		self.poke(self.OPorts[0], self.msg)
		
	###
  	def timeAdvance(self): return self.state['sigma']

	###
	def __str__(self):return "Integrator3"
	
