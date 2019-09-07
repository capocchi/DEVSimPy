# -*- coding: utf-8 -*-

"""
Name : To_Pusher.py
Brief descritpion : Atomic Model pushing results to a web socket
Author(s) : Celine KESSLER
Version :  2.0
Last modified : 12/05/2016
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

### just for python 2.5


from QuickScope import *

import random
from decimal import *
import os
from datetime import datetime
import pusher
import json

#  ================================================================    #
class To_Pusher(QuickScope):
	"""	Atomic Model writing on the disk.
	"""

	###
	def __init__(self, app_id='178867', key='c2d255356f53779e6020', secret='9d41a54d45d25274df63', pusherChannel='mySimu'):
		""" Constructor.

			@param app_id  : PUSHER identifier
			@param key     : PUSHER key
			@param secret  : PUSHER secret key--> from PUSHER subscription
			@param channel : PUSHER channel identifier
			@param event   : PUSHER event identifier

		"""
		QuickScope.__init__(self)

		#decimal precision
		getcontext().prec = 6

		### last time value for delete engine
		'''self.last_time_value = {}
		self.buffer = {}'''

		### Interface with the web socket broker : Pusher
		self.app_id = app_id
		self.key = key
		self.secret = secret
		self.pusher = pusher.Pusher(app_id=self.app_id,key=self.key,secret=self.secret,ssl=True,port=443)
		#self.pusher_data = []
		#self.push_time = datetime.today()
		self.pusherChannel = pusherChannel
		self.event = 'results'

	###
	def extTransition(self, *args):
		"""
		"""

		n = len(self.IPorts)

		for np in range(n):
			### adapted with PyPDEVS
			if hasattr(self, 'peek'):
				msg = self.peek(self.IPorts[np])
			else:
				inputs = args[0]
				msg = inputs.get(self.IPorts[np])

			### init last_time
			'''if self.timeLast == 0 and self.timeNext == INFINITY:
				self.last_time_value[np] = 0.0

			### init buffer
			if np not in self.buffer.keys():
				self.buffer[np] = 0.0'''

			if msg:

				# if step axis is chosen ...
				
				### adapted with PyPDEVS
				if hasattr(self, 'peek'):
					t = float(msg.time)
					val = msg.value[0]
				else:
					t = float(msg[1][0])
					val = msg[0][0]

				if isinstance(val, int) or isinstance(val, float):
					v = float(val)
				else:
					v = val

				result = {'time':t, 'value':v}
				print(result)
				self.pusher.trigger(self.pusherChannel, self.event, json.dumps(result))
				#self.pusher_data.append({'label': str(t), 'value':str(v)})
				
				#self.last_time_value[fn] = t
				#self.buffer[fn] = v"""

				del msg

		self.state["sigma"] = 0
		return self.state

	def intTransition(self):
	    """now = datetime.today()
	    if (len(self.pusher_data) == 50) or (now - self.push_time).seconds >= 1:
			self.pusher.trigger(self.channel, self.event, json.dumps(self.pusher_data))
			print('PUSH')
			del self.pusher_data[:]
			self.push_time = now
	    self.state["status"] = 'IDLE'"""
	    self.state["sigma"] = INFINITY
	    return self.state

	def finish(self, msg):
		#self.pusher.trigger(self.channel, self.event, json.dumps(self.pusher_data))
		pass
	###
	def __str__(self):return "To_Pusher"
