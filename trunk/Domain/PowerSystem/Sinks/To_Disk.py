# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# To_Disk.py --- Atomic Model writing results in text file on the disk
#                     --------------------------------
#                        	 Copyright (c) 2009
#                       	  Laurent CAPOCCHI
#                      		University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 21/03/09
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

from QuickScope import *

from decimal import *
import os.path

#  ================================================================    #
class To_Disk(QuickScope):
	"""	Atomic Model writing on the disk.
	"""

	###
	def __init__(self, fileName = os.path.join(os.getcwd(),"result"), eventAxis = False):
		QuickScope.__init__(self)
		
		# local copy
		self.fileName = fileName

		#decimal precision
		getcontext().prec = 6
		
		self.ea = eventAxis

	###
	def extTransition(self):
		
		activePort = self.myInput.keys()[0]
		np=activePort.myID
		msg= self.peek(activePort)

		# if step axis is choseen
		if self.ea:
			self.ea += 1
			t = self.ea
		else:
			t = Decimal(str(float(msg.time)))

		v = Decimal(str(float(msg.value[0])))
				
		# ecriture dans la liste pour affichier le QuickScope et le SpreadSheet
		# si il y a eu un changement du nombre de ports alors on creer la nouvelle entre dans results (on ne regenere pas d'instance)
		try:
			self.results[np].append((t,v))
		except KeyError:
			self.results.update({np:[(t,v)]})

		try:
			filePath = "%s%d.dat"%(self.fileName,np)
			f = open(filePath,'wa')
		except IOError:
			f = open(filePath,'w')

		f.write("%s %s\n"%(t,v))
		f.close()
	
		self.state["sigma"] = 0

	###
	def __str__(self):return "To_Disk"
