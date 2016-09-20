# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
 Name:          <Process.py>
 Model:         Execute external process into external transition fonction
 Authors:       L. Capocchi <capocchi@univ-corse.fr>
 Organization:  UMR CNRS 6134
 Date:          06.15.2016
 License:       GPL V3.0
-------------------------------------------------------------------------------
"""

### Specific import ------------------------------------------------------------
from DomainInterface.DomainBehavior import DomainBehavior
from DomainInterface.Object import Message

import subprocess
import os

### Model class ----------------------------------------------------------------
class Process(DomainBehavior):
	''' DEVS Class for Process model
	'''

	def __init__(self, filename="file.py", wait=True):
		''' Constructor.

			@param filename : path of the python file to execute.
			@param wait : if true, wait until process is over
		'''
		DomainBehavior.__init__(self)

		### local coyp
		self.process_file = filename
		self.wait = wait

		self.msg = [None]*len(self.IPorts)

		self.state = {	'status': 'IDLE', 'sigma':INFINITY}

	def extTransition(self):
		''' DEVS external transition function.
		'''

		for i in range(len(self.IPorts)):
			msg = self.peek(self.IPorts[i])
			if msg:
				self.msg[i] = msg

		if not (None in selg.msg):
			self.state['sigma'] = 0
			self.state['status'] = 'PROCEED'
		else:
			self.state['sigma'] = INFINITY
			self.state['status'] = 'WAIT'

	def outputFnc(self):
		''' DEVS output function.
		'''
		if self.state['status'] == 'PROCEED' and os.path.isfile(self.process_file):
			args = [ msg.value for msg in self.msg]
			
			process = subprocess.Popen(['python', self.process_file]+args, stdout=subprocess.PIPE)
			if self.wait:
				process.wait()
			out = process.communicate()[0]
			
			self.poke(self.OPorts[0], Message(out, self.timeNext))

	def intTransition(self):
		''' DEVS internal transition function.
		'''
		self.state['sigma'] = INFINITY
		self.state['status'] = 'IDLE'

	def timeAdvance(self):
		''' DEVS Time Advance function.
		'''
		return self.state['sigma']

	def finish(self, msg):
		''' Additional function which is lunched just before the end of the simulation.
		'''
		pass
