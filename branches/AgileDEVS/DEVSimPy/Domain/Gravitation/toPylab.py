# -*- coding: utf-8 -*-
import pylab

from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message
# import pickle

class toPylab(DomainBehavior):
	
	def __init__(self, fusion = True, eventAxis = False):
		""" Constructor.
			@param fusion : Flag to plot all signals on one graphic
			@param eventAxis : Flag to plot depending event axis
		"""
		DomainBehavior.__init__(self)
		self.state = {'status': 'FREE', 'sigma':0}
		
		# fusioning curve
		self.fusion = fusion
		# replace time axis with step axis
		self.eventAxis = eventAxis
		# results tab (results attribut must be defined in order to plot the data)
		self.results = {} #OrderedDict()
		self.t=INFINITY
		self.xl = []
		self.yl = []
		self.list={}
		
	

	def extTransition(self):
		for i in xrange(len(self.IPorts)):
			msg = self.peek(self.IPorts[i])
			if msg:
				M = msg.value[0]
				x = msg.value[1]
				y = msg.value[2]
				myID = msg.value[3]
				if not myID in self.list:
					self.list[myID] = ([], [])
				
				tup = self.list[myID]
				xl=tup[0]
				xl.append(x)

				yl=tup[1]
				yl.append(y)
		

	def outputFnc(self):
		pass

	def intTransition(self):
		self.state["sigma"] = INFINITY
		

	def timeAdvance(self):
		''' DEVS Time Advance function.
		'''
		return self.state['sigma']
		
	# def finish(self, msg):
	# 	for k in self.list:
	# 		tup = self.list[k]
	# 		# print k, len(tup[0])
	# 		# print k, len(tup[1])
	# 		pylab.plot(tup[0], tup[1])
	# 	pylab.show()
		