# -*- coding: utf-8 -*-

"""
Name : To_Disk.py
Brief descritpion : Atomic Model writing results in text file on the disk
Author(s) : Laurent CAPOCCHI <capocchi@univ-corse.fr>
Version :  2.0
Last modified : 29/10/20
GENERAL NOTES AND REMARKS:
GLOBAL VARIABLES AND FUNCTIONS:
"""

from QuickScope import *
import random
from decimal import *
import os
import tempfile

def append_new_line(file_name, text_to_append):
	"""Append given text as a new line at the end of file"""
	# Open the file in append & read mode ('a+')
	with open(file_name, "a+") as file_object:
		# Move read cursor to the start of file.
		file_object.seek(0)
		# If file is not empty then append '\n'
		data = file_object.read(100)
		if len(data) > 0:
			file_object.write("\n")
		# Append text at the end of file
		file_object.write(text_to_append)

#  ================================================================    #
class To_Disk(QuickScope):
	"""	Atomic Model writing on the disk.
	"""

	###
	def __init__(self, fileName = "result", eventAxis = False, comma = " ", ext = '.dat', col = 0):
		""" Constructor.

			@param fileName : Name of output fileName
			@param eventAxis : Flag to plot depending events axis
			@param comma : Comma symbol
			@param ext : Output file extension
			@param col : Considered column
		"""
		QuickScope.__init__(self)

		### a way to overcome the random initialization of the fileNam attr directly in the param list of the constructor!
		fileName = fileName if fileName!= 'result' else os.path.join(tempfile.gettempdir(),"result%d"%random.randint(1,100000))

		# local copy
		self.fileName = fileName
		self.comma = comma
		self.ext = ext
		self.col = col
		
		#decimal precision
		getcontext().prec = 6

		### last time value for delete engine and
		self.last_time_value = {}

		self.buffer = {}

		### buffer position with default lenght 100
		#self.pos = [-1]*100

		### event axis flag
		self.ea = eventAxis

		### remove old files corresponding to 1000 presumed ports
		for np in range(1000):
			fn = "%s%d%s"%(self.fileName, np, self.ext)
			if os.path.exists(fn):
				os.remove(fn)
	###
	def extTransition(self, *args):
		"""
		"""

		n = len(self.IPorts)
		#if len(self.pos) > n:
		#	self.pos = self.pos[0:n]

		for np in range(n):
			### adapted with PyPDEVS
			if hasattr(self, 'peek'):
				msg = self.peek(self.IPorts[np])
			else:
				inputs = args[0]
				msg = inputs.get(self.IPorts[np])

			### filename
			fn = "%s%d%s"%(self.fileName, np, self.ext)

			### remove all old file starting
			if self.timeLast == 0 and self.timeNext == INFINITY:
				self.last_time_value[fn] = 0.0

			### init buffer
			if fn not in list(self.buffer.keys()):
				self.buffer[fn] = 0.0

			if msg:
				# if step axis is choseen
				if self.ea:
					self.ea += 1
					t = self.ea
					self.last_time_value.update({fn:-1})
				else:

					if fn not in self.last_time_value:
						self.last_time_value.update({fn:1})

					### adapted with PyPDEVS
					if hasattr(self, 'peek'):
						t = Decimal(str(float(msg.time)))
					else:
						t = Decimal(str(float(msg[-1][0])))
				
				### adapted with PyPDEVS
				
				val = msg.value[self.col] if hasattr(self, 'peek') else msg[0][self.col]
				
				if isinstance(val, int) or isinstance(val, float):
					v = Decimal(str(float(val)))
				else:
					v = val
				
			
				if t != self.last_time_value[fn]:
					append_new_line(fn,"%s%s%s"%(self.last_time_value[fn],self.comma,self.buffer[fn]))
					#with open(fn, 'a') as f:
					#	f.write("%s%s%s\n"%(self.last_time_value[fn],self.comma,self.buffer[fn]))
					self.last_time_value[fn] = t
				
				self.buffer[fn] = v
				
				### run only with python 2.6
				#with open(fn, 'a') as f:

				#	if t == self.last_time_value[fn]:
				#		if self.pos[np] == -1:
				#			self.pos[np] = 0
				#		f.seek(self.pos[np], os.SEEK_SET)
				#		f.truncate(self.pos[np])

				#	else:
				#		self.pos[np] = f.tell()						
				#		self.last_time_value[fn] = t

				#	f.write("%s%s%s\n"%(t,self.comma,v))
					
				del msg

		self.state["sigma"] = 0
		return self.state

	def finish(self, msg):
		n = len(self.IPorts)
		for np in range(n):
			fn = "%s%d%s"%(self.fileName, np, self.ext)
			if (fn in self.last_time_value) and (fn in self.buffer):
				append_new_line(fn,"%s%s%s"%(self.last_time_value[fn],self.comma,self.buffer[fn]))
#				with open(fn, 'a') as f:
#					f.write("%s%s%s\n"%(self.last_time_value[fn],self.comma,self.buffer[fn]))

	###
	def __str__(self):return "To_Disk"
