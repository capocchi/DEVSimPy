# -*- coding: utf-8 -*-

from Domain.Myths.MythDomainBehavior import MythDomainBehavior
from Domain.Myths.Object import *

class Generator(MythDomainBehavior):
	""" Generates actions
	"""
	
	# all arguments should be strictly positive integers
	def __init__(self,ia=None,ib=None,name=None):
		
		MythDomainBehavior.__init__(self)
		# Always call parent class' constructor FIRST:
		self.ia=ia
		self.ib=ib
		
		# add one output port
		#self.OUT = self.addOutPort()
		self.state=GeneratorState(first=True)
		if repcharg == "n":
			listesauv.append(self)
		# Alternative:
		# self.elapsed = arbitrary_number
	
	def intTransition(self):
		self.state.first = False 
		return self.state
	
	def outputFnc(self):
		print "executer actions? (y/n) "
		answer1 = input()
		if answer1 == "y":
			repaction = ""
			term1 = ""
			term2 = ""
			term3 = ""
			term4 = ""
			term5 = 0
			listeactions = []
			i = 0
			nba = 0
			print "Nombre d'actions � executer?"
			nba = input()
			while i<nba:
				i = i + 1
			
			print "action generator"
			
			print "quelle action?"
			print "Numero "
			print i
			print "vous avez le choix entre :"
			print "(h)omologie"
			print "(i)nversion"
			print "(s)ym�trie"
			print "(o)pposition"
			print "(f)ormule canonique"
			print "(p) transformation putiphar"
			print "(l) last form of the CF"
			repaction = input()
		if repaction == "h":
			act = 1
			print "Avec quel terme doit-on effectuer l'homologie?"
			term1 = input ()
			print "Quel et le nouveau terme apres homologie?"
			term2 = input ()
		elif repaction == "i":
			act = 2
			print "Avec quel terme doit-on effectuer l'inverion?"
			term1 = input ()
		elif repaction == "s":
			act = 3
			print "Avec quel terme doit-on effectuer la sym�trie?"
			term1 = input ()
		elif repaction == "o":
			act = 4
			print "Avec quel terme doit-on effectuer l'opposition?"
			term1 = input ()
		elif repaction == "f":
			act = 5
			print "Quel myth�me est concern�?"
			term5 = input()
		elif repaction == "p":
			act = 6
			print "Quel myth�me est concern�?"
			term5 = input()
		elif repaction == "l":
			act = 6
			print "Quel myth�me est concern�?"
			term5 = input()
		
		
		listeactions.append((act,term1,term2,term3,term4,term5))
		
		act = action(act,listeactions)        
		# In pythonDEVS, event objects are "poke"d on output ports
		# in the outputFnc. Conversely, in the extTransition
		# function, it is possible to "peek" input ports for incoming
		# event objects. This deviates from classic DEVS which 
		# does not have ports.
		self.poke(self.OPorts[0], act)
	
	
	def timeAdvance(self):
		if self.state.first == True:
			return 0
		else:
			return uniform(self.ia, self.ib)
	 
	def __str__(self):
		return "Generator"