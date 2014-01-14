# -*- coding: iso-8859-1 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Hsaturation.py --- Saturation horizontal
#                     --------------------------------
#                        	 Copyright (c) 2007
#                       	  Laurent CAPOCCHI
#                      		University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 21/03/07
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GLOBAL VARIABLES AND FUNCTIONS
#
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

try:
	from DomainInterface.DomainBehavior import DomainBehavior, Master
	from DomainInterface.Object import Message
except ImportError:
	import sys,os
	for spath in [os.pardir+os.sep,"../../../Lib"]:
		if not spath in sys.path: sys.path.append(spath)
	from DomainInterface.DomainBehavior import DomainBehavior, Master
	from DomainInterface.Object import Message

#    ======================================================================    #

from math import sqrt

class Hsaturation(DomainBehavior):
	'''	Model atomique de la fonction "marche"
	'''

	###
	def __init__(self, xl=1, xu=-1):
		'''	Constructeur
		'''
		DomainBehavior.__init__(self)

		# Declaration des variables d'état (actif tout de suite)
		self.state = {	'status':	'ACTIVE',
						'sigma':	Master.sdb.INFINITY}
		# Local copy
		self._xl=xl
		self._xu=xu
		
		self.ul=(self._xl+self._xu)/2
		self.Y=[0]*3
		self.u=0
		self.mu=0
		self.pu=0
		# Declaration du port d'entrée et de sortie
		
		self.OUT = self.addOutPort()
		self.IN = self.addInPort()
		
	###
  	def intTransition(self):
		
		if self.state['sigma'] !=0:
			self.u+=self.mu*self.state['sigma']+self.pu*self.state['sigma']*self.state['sigma'];
			self.mu+=2*self.pu*self.state['sigma'];
			if( self.u<((self._xu+self._xl)/2) ):
				self.u=self._xl
			else:
				self.u=self._xu
		
		a=0.0
		b=0.0
		c=0.0
		s=[Master.sdb.INFINITY]*2
		sol=[Master.sdb.INFINITY]*2
		
		for i in range(2):
			if i==0:
				c=self.u-self._xl
			else:
				c=self.u-self._xu
			if a==0:
				if b!=0:
					s[0]=-c/b
			else:
				if b*b>=4*a*c:
					s[0]=(-b+sqrt(b*b-4*a*c))/(2*a);
					s[1]=(-b-sqrt(b*b-4*a*c))/(2*a);
			if s[0]<=0:
				s[0]=Master.sdb.INFINITY
			if s[1]<=0:
				s[1]=Master.sdb.INFINITY
			if s[0]<s[1]:
				sol[i]=s[0]
			else:
				sol[i]=s[1]
				
		if(sol[0]<sol[1]):
			self.state['sigma']=sol[0]
		else:
			self.state['sigma']=sol[1]
		
		return self.state
	
	###
	def extTransition(self):
		
		self.msg=self.peek(self.IN)
		
		self.u1=self.u+self.mu*self.elapsed+self.pu*self.elapsed*self.elapsed
		self.u, self.mu, self.pu=self.msg.value
		self.level=[1]*2
		
		if(self.u1<self._xl):	self.level[0]=0
		elif(self.u1>self._xu):	self.level[0]=2
		
		if(self.u<self._xl):	self.level[1]=0
		elif(self.u>self._xu):	self.level[1]=2
		
		if( ((self.u<=self._xu)and(self.u>=self._xl)) or (self.level[0]!=self.level[1])):
			self.state['sigma']=0
		else:
			sol=[0]*2
			s=[0]*2
			a=self.pu
			b=self.mu
			c=0.0
			
			s[0]=s[1]=Master.sdb.INFINITY
			sol[0]=sol[1]=Master.sdb.INFINITY
			for i in range(2):
				if(i==0):
					c=self.u-self._xu
				else:
					c=self.u-self._xl
				if(a==0):
					if(b!=0):
						s[0]=-c/b
				else:
					if(b*b>=4*a*c):
						s[0]=(-b+sqrt(b*b-4*a*c))/(2*a)
						s[1]=(-b-sqrt(b*b-4*a*c))/(2*a)
	
				if(s[0]<=0):s[0]=Master.sdb.INFINITY
				if(s[1]<=0):s[1]=Master.sdb.INFINITY
				if(s[0]<s[1]):sol[i]=s[0]
				else:sol[i]=s[1]
				
			if(sol[0]<sol[1]):
				self.state['sigma']=sol[0]
			else:
				self.state['sigma']=sol[1]
		
		return self.state
		
	###
  	def outputFnc(self):
		
		# envoie du message le port de sortie
		if( (self.state['sigma']!=0)or(self.level[1]!=1) ):
			if( (self.u+self.mu*self.state['sigma']+self.pu*self.state['sigma']*self.state['sigma'])>((self._xl+self._xu)/2) ):
				self.Y[0]=self._xu
			else:
				self.Y[0]=self._xl
		else:
			self.Y[0]=self.u
		
		self.Y[1]=self.mu+2*self.pu*self.state['sigma']
		self.Y[2]=self.pu
		if( (self.Y[0]==self._xu) and ( (self.Y[1]>0) or ( (self.Y[1]==0)and(self.Y[2]>0) ) ) ):
			self.Y[1]=0
			self.Y[2]=0
		else:
			if( (self.Y[0]==self._xl) and ( (self.Y[1]<0) or ( (self.Y[1]==0)and(self.Y[2]<0) ) ) ):
				self.Y[1]=0
				self.Y[2]=0
		
		self.poke(self.OUT, Message(self.Y,self.timeNext))

	###
  	def timeAdvance(self):

		if Master.sdb.VERBOSE:print '\x1B[1;34;40m %s ta \x1B[0;37;40m'%self.__str__()
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = Master.INFINITY):
		self.state = { 'status':status, 'sigma':sigma}

	###
	def __str__(self):return "Switch3"
