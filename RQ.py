# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        <RQ.py>
#
# Model:       <Buffer Queue>
# Author:      <Samuel TOMA>
#
# Created:     <2010-03-24>
#-------------------------------------------------------------------------------

from .DomainInterface.DomainBehavior import DomainBehavior 
from Object import Message

### Model class ----------------------------------------------------------------
class RQ(DomainBehavior):

	 def __init__(self):
		DomainBehavior.__init__(self)
		self.state = {'status': 'INACTIF', 'sigma': INFINITY}
		self.phase = 'Free'
		self.jobsList = []
		
	 def intTransition(self):
		self.state['sigma'] = INFINITY
		self.state['status'] = 'IDLE'

	 def extTransition(self):
		np=0
		self.msg= self.peek(self.IPorts[np])
		while(self.msg == None):
			np+=1
			self.msg= self.peek(self.IPorts[np])

		if np == 0 :
			# we add to the job list a new job that is formed of the arrival time and the time that it needs to be executed in the CPU
			self.jobsList.insert(0,[self.msg.value,self.msg.time])
			if self.phase == 'Free':
				self.state['status'] = 'ACTIF'
				self.state['sigma'] = 0.01
		else:
			self.phase = 'Free'
			self.state['status'] = 'ACTIF'
			self.state['sigma'] = 0.01

	 def outputFnc(self):
		# we verify that we have a job and CPU is free then we send a message that contains the execution time and the sent time
		if (len(self.jobsList) > 0 and self.phase == 'Free'):
			job = self.jobsList.pop()
			job[1] = self.timeNext
			self.poke(self.OPorts[0],Message(job[0],job[1]))
			self.phase = 'Busy'

	 def timeAdvance(self):
		return self.state['sigma']
