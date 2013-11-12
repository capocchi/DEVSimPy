# -*- coding: utf-8 -*-

"""
Name : To_Disk.py
Brief descritpion : Atomic Model writing results in text file on the disk
Author(s) : Laurent CAPOCCHI <capocchi@univ-corse.fr>
Version :  2.0
Last modified : 21/03/09
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

### just for python 2.5
from __future__ import with_statement

from Domain.Myths.MythDomainBehavior import MythDomainBehavior
import random
from decimal import *
import os

#  ================================================================    #
class Observor(MythDomainBehavior):
	"""	Atomic Model writing on the disk.
	"""

	###
	def __init__(self, fileName = os.path.join(os.getcwd(),"result%d"%random.randint(1,100)), eventAxis = False, comma = " ", ext = '.dat', col = 0):
		""" Constructor.

			@param fileName : name of output fileName
			@param eventAxis : flag to plot depending events axis
			@param comma : comma symbol
			@param ext : output file extension
			@param col : considered coloum
		"""
		MythDomainBehavior.__init__(self)

		self.state = {'status':'IDLE', 'sigma':INFINITY}
			
		# local copy
		self.fileName = fileName
		self.comma = comma
		self.ext = ext
		self.col = col

		#decimal precision
		getcontext().prec = 6

		### last time value for delete engine and
		self.last_time_value = {}

		### buffer position with default lenght 100
		self.pos = [-1]*100
		### event axis flag
		self.ea = eventAxis

	###
	def extTransition(self):
		"""
		"""

		n = len(self.IPorts)
		if len(self.pos) > n:
			self.pos = self.pos[0:n]

		for np in xrange(n):

			msg = self.peek(self.IPorts[np])

			if msg:

				### filename
				fn = "%s%d%s"%(self.fileName, np, self.ext)

				# if step axis is choseen
				if self.ea:
					self.ea += 1
					t = self.ea
					self.last_time_value.update({fn:-1})
				else:

					if fn not in self.last_time_value:
						self.last_time_value.update({fn:1})

					t = Decimal(str(float(msg.time)))

					if float(t) == 0.0 and self.timeLast == 0 and self.timeNext == INFINITY and os.path.exists(fn):
						self.last_time_value[fn] = 0.0
						os.remove(fn)

				val = msg.value[self.col]
				if isinstance(val, int) or isinstance(val, float):
					v = Decimal(str(float(val)))
				else:
					v = val

				### run only with python 2.6
				with open(fn, 'a') as f:
					try:
						for elem in msg.value:
							f.write("%s%s%s%s%s\n"%(elem[0],self.comma,elem[1],self.comma,elem[2]))
					except Exception, info:
						pass

		self.state["sigma"] = 0

	def intTransition(self):
			self.state["status"] = 'IDLE'
			self.state["sigma"] = INFINITY

	###
	def timeAdvance(self):return self.state['sigma']

	###
	def __str__(self):return "Observor"
