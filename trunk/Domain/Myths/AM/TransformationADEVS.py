# -*- coding: utf-8 -*-

from Domain.Myths.MythDomainBehavior import MythDomainBehavior
from Domain.Myths.Object import*
	
class TransformationADEVS(MythDomainBehavior) :
	"""Sample Atomic-DEVS descriptive class.
	"""
	
	###
	def __init__(self, myths=None, fonction=None, liste=None, currentST=None , numdep=1):
		"""Constructor (parameterizable).
		Giving a name (string) to a model is not mandatory
		(a globally unique name "A<i>" is assigned by default).
		If a name is given, the simulation trace becomes far more
		readable.
		"""
		
		# Always call parent class' constructor FIRST:
		MythDomainBehavior.__init__(self)
		
		#local copy
		self.myths=myths
		self.fonction=fonction
		self.liste=liste
		self.currentST=currentST
		
		mythdep = numdep
		#mythdep = "st%s" % numdep 
	
		#f= open('fichiermythes','w')
		self.state = TransformationADEVSState(myths = [], fonction = [], liste = [], currentST = mythdep, active = mythdep - 1)
		
		if repcharg == "n":
			listesauv.append(self.state)
		
		#pickle.dump(self.state,f)
		# TOTAL STATE:
		#  Define 'state' attribute (initial sate):
		#print "commbien de mythes voulez-vous?"
		#nmyths = input()
		#ll = []
		#for i in range(1,nmyths):
		# tmpName = "st%s" % i
		# tmp = self.addSubModel(MythvariantCDEVS(name=tmpName))
		# ll = ll + [tmp]
		
		# self.list = TransformationADEVSState(self,list=ll)
		# self.currentST = list[1]
		
		# ELAPSED TIME:
		#  Initialize 'elapsed time' attribute if required.
		#  (by default (if not set by user), self.elapsed is initialized to 0.0)
		self.elapsed = 0.0
		#  With elapsed time for example initially 1.1 and 
		#  this SampleADEVS initially in 
		#  a state which has a time advance of 60,
		#  there are 60-1.1 = 58.9 time-units remaining until the first 
		#  internal transition 
		
		# HV: check in simulator that elapsed can not be larger than
		# timeAdvance
		
		# PORTS:
		#  Declare as many input and output ports as desired
		#  (usually store returned references in local variables):

		#pickle.dump(self.IN,f)
		#pickle.dump(self.OUT,f)
		#f.close()
  ###
 	def extTransition(self) :
		"""External Transition Function."""
		
		# Compute and return the new state based (typically) on current
		# State, Elapsed time parameters and calls to 'self.peek(self.IN)'.
		# When extTransition gets invoked, input has arrived
		# on at least one of the input ports. Thus, peek() will
		# return a non-None value for at least one input port.
		
		
		
		#print self
		# print self.state
		a = self.state.currentST
		# print a
		evenemt = self.peek(self.IN)
		# print "event"
		# print evenemt
		# print "current state"
		# print self
		# print "etce cela?"
		#print self.state.currentST
		# print "oui oui"
		self.state.fonction.append(evenemt.transf)
		# print self.state.fonction
		# print "non non"
		# print evenemt.ID
		# print evenemt.transf
		# print "oui oui"
		print "param"
		print evenemt.param
		
		print "fonction"
		
		print self.state.fonction
		
		print "le mythe courant est le suivant :"
		print self.state.currentST
		i = 0
		#print len(teta)
		#print teta[0]
		#print teta[0][0]
		#while i < len(teta):
		# if self.state.currentST == teta[i][0]:
		#  myth = teta[i][1]
		#  i = len(teta)
		# i = i + 1
		longactions = 0
		longactions =  len (evenemt.param)
		print longactions
		# longactions = longactions - 1
		print evenemt.param
		
		j = 0
	
		print "le mythe courant est le suivant :"
		print "ATTENTION"
		print self.state.currentST
		print self.state
		print self
		print self.state.myths[0]
		print "il  est compos� de "
		print self.parent.dynamicComponentSet
		myth = self.parent.dynamicComponentSet[self.state.currentST - 1]
		print "MYTHE !!!"
		print myth
		l = len(myth.componentSet)
		print l
		print "myth�me (s)"
		i = 0
		print "le mythe est donc:"
		while i < l:
			print myth.componentSet[i].a
			print "poss�de"
			print myth.componentSet[i].x
			i = i + 1
		modif = 1
		nummyth = self.state.currentST-1
		mythcourant = myth
		print self.state.currentST
		na = "mythe%s" % (self.state.currentST+1)
		print na
		print self.parent
		#ERREUR SUB = self.parent.addSubModel(MythvariantbisCDEVS(name=na))
		SUB = MythvariantCDEVS(name=na)
		newmodel = SUB
		print "!!!!attention!!!!"
		print self.parent
		prevport = SUB.IN
		print "l(a)es transformation(s) suivante(s) es(son)t appliqu�e(s):"
		while j < longactions:     
			if evenemt.param[j][0] ==1:
				print "homologie entre "
				print evenemt.param [j][1]
				print "et"
				print evenemt.param [j][2]
				listeret = homologie (mythcourant,newmodel,evenemt.param [j][1],evenemt.param [j][2],newmodel.IN,na) 
				prevport = listeret[0]
				mythcourant = listeret[1]
				print "homologie"
				print prevport
				print mythcourant
				print SUB
		
			if evenemt.param[j][0] ==2:
				print "inversion du terme"
				print evenemt.param [j][1]
				mythcourant = inversion(mythcourant,evenemt.param [j][1])
	
			if evenemt.param[j][0] ==3:
				print "symetrie entre "
				print evenemt.param [j][1]
				print "et"
				print evenemt.param [j][2]
				mythcourant = symetrie(mythcourant,evenemt.param [j][1],evenemt.param [j][2])
			
			if evenemt.param[j][0] ==4:
				print "opposition du terme"
				print evenemt.param [j][1]
				mythcourant = oppostion(mythcourant,evenemt.param [j][1])
			
			if evenemt.param[j][0] ==5:
				print "formule canonique appliqu�e sur le myth�me : "
				print evenemt.param [j][4]
				mythcourant = fc (myth,evenemt.param [j][4])
			
			if evenemt.param[j][0] ==6:
				print "transformation putiphar appliqu�e sur le myth�me :"
				print evenemt.param [j][4]
				mythcourant = putiphar (myth,evenemt.param [j][4])
			print "boucle"
			print j
			print mythcourant
			print prevport
			if j != 1:
				na = "mythe%s" % (self.state.currentST+1)
				newmodel = MythvariantCDEVS(name=na)
				j = j + 1
		#ATTENTION ERREUR mythcourant.connectPorts(prevport, mythcourant.OUT)
		print "myth courant connect port fait"
		self.state.currentST =  self.state.currentST + 1
		#ATTENTION ERREUR self.state.myths.append(mythcourant)
		#remplacer self par myhticalthought
		self.parent.dynamicComponentSet.append(SUB)
		print "IC"
		print mythcourant.IC
		print "EOC"
		print mythcourant.EOC
		self.parent.dynamicIC.append(mythcourant.IC)
		self.parent.dynamicEOC.append(mythcourant.EOC)
		self.parent.dynamicEIC.append (mythcourant.EIC)
		supervis = self.parent.supervisor
		print "supervis"
		print supervis
		#erreur supervis.state.myths.append(mythcourant)  
		# � remettre 2 self.parent.connectPorts(supervis.OUT, mythcourant.IN)
		#mythanc = self.state.myths[self.state.currentST-2]
		#self.parent.disconnectPorts(supervis.OUT,mythanc.IN)
		#self.parent.disconnectPorts(mythanc.OUT,mythanc.IN)
		#self.parent.disconnectPorts(supervis.OUT,mythanc.IN)
		print "connect ports 2 fait"
		# � remettre 2 self.parent.connectPorts(mythcourant.OUT, self.parent.OUT)
		
		# a remettre self.parent.disconnectPorts(mythanc.OUT, self.parent.OUT)
		transf = self.parent.componentSet[0]
		print "TRANSF���"
		print transf
		#a remettre self.parent.disconnectPorts(transf.OUT,mythanc.IN)
		i = 0
		
		print "current state"
		print self.state.currentST
		# ATTENTION ERREUR ind = self.state.currentST - 1
		print "ind"
		# ATTENTION ERREUR print ind
		# ATTENTION ERREUR myth = self.state.myths[ind]
		l = len(SUB.componentSet)
		print l
		print "myth�me (s)"
		k = 0
		print "le mythe est donc:"
		while k < l:
			print SUB.componentSet[k].a
			print "poss�de"
			print SUB.componentSet[k].x
			k = k + 1
		print "self.state.currentST"
		print supervis.state.myths
		return self.state

	def __str__(self):
		return "TransfomationADEVS"