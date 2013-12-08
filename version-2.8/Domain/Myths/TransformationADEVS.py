# -*- coding: utf-8 -*-

### at the beginning to prevent with statement for python vetrsion <=2.5
from __future__ import with_statement

import os

from Domain.Myths.MythDomainBehavior import MythDomainBehavior
from Domain.Myths.Object import Myth

### if OUT_DIR is not define (if this class is used out of DEVSimPy)
try:
	eval("OUT_DIR")
except:
	cwd = os.getcwd()
	OUT_DIR = 'out'
	path = os.path.join(cwd,OUT_DIR)
	if not os.path.isdir(path):
		## creating the out default directory
		os.mkdir(path)

class TransformationADEVS(MythDomainBehavior) :
	"""
	"""

	###
	def __init__(self, transfoList=[]):
		"""Constructor.

			transfoList = [(M2, ('h', 'toto', 'titi'))] ordered by the port number.
		"""

		MythDomainBehavior.__init__(self)

		#local copy
		self.transfoList = transfoList

		self.state = {'status':'IDLE', 'sigma':INFINITY}

		self.msg = None
		self.p = None

	###
	def intTransition(self):
		# Changement d'etat
		self.state['sigma'] = INFINITY

	###
	def extTransition(self):

		# multi-port values version
		for p in range(len(self.IPorts)):
				msg = self.peek(self.IPorts[p])
				if msg != None:
						self.msg = msg
						self.p = p

		current_myth = self.msg.value[0]
		result = current_myth.mythemsList
		#print "result"
		#print result

		new_myth_name = self.transfoList[self.p][0]

#		print "transfolist"
		#print self.transfoList[self.p]
		#print self.transfoList[self.p][1]

		for rule in self.transfoList[self.p][1]:

			p1,p2 = rule[1:]
			a = map(lambda t: t[0], result)
#			print "a"
#			print a
			x = map(lambda t: t[1], result)
#			print "x"
#			print x


			### 'h|i|o|s', p1=a1, p2=a2
			if rule[0] in ('h','i','o', 's'):
				a = [ p2 if v == p1 else v for v in a ]
				result = map(lambda ai,xi: (ai,xi), a, x)

				### 'hf|if', p1=b1, p2=b2
			if rule[0] in ('hf','if'):
				y = [ p2 if v == p1 else v for v in x ]
				result = map(lambda bi,yi: (bi,yi), a, y)

			### 'a',p1=pos,p2=new_mythem
			elif rule[0] in ('a'):
				result.insert(p1+1, p2)
			### 'f1', p1=pos, p2=inv
			elif rule[0] in ('f1'):
				a,x = result[p1]
				b,y = result[p1+1]
				result[p1] = (b,x)
				result[p1+1] = (y,p2)
			### 'f3', p1=pos, p2=inv
			elif rule[0] in ('f2'):
				a,x = result[p1]
				b,y = result[p1+1]
				result[p1] = (b,a)
				result[p1+1] = (y,p2)
			### 'f3', p1=pos, p2=inv
			elif rule[0] in ('f3'):
				a,x = result[p1]
				b,y = result[p1+1]
				result[p1] = (b,y)
				result[p1+1] = (x,p2)
			### 'd', p1=pos
			elif rule[0] in ('d'):
				map(lambda p: result.remove(result[p]),p1)

		### TODO:ajouter la reation de rep
		with open(os.path.join(HOME_PATH, OUT_DIR,"%s.dat"%new_myth_name),'w') as f:
			for t in result:
				f.write("%s %s \n"%(t[0],t[1]))

		### myth generation
		self.msg.value[0] = Myth(new_myth_name,current_myth.name,result)

		# changement d'etat
		self.state['status']='ACTIF'
		self.state['sigma'] = 0

	###
	def outputFnc(self):
		assert(self.msg!=None)

		self.msg.time=self.timeNext

		# envoie du message sur les ports de sortie
		self.poke(self.OPorts[self.p], self.msg)

	###
	def timeAdvance(self):
		return self.state['sigma']

	def __str__(self):
		return "TransfomationADEVS"
