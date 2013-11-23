# -*- coding: utf-8 -*-

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# Converter.py --- Base converter 
#                     --------------------------------
#                        	 Copyright (c) 2011
#                       	  Laurent CAPOCCHI
#                      		University of Corsica
#                     --------------------------------
# Version 1.0                                        last modified: 04/04/11
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

from DomainInterface.DomainBehavior import DomainBehavior
from itertools import *
from utilities import *

#    ======================================================================    #
class Converter(DomainBehavior):
	'''	Base Converster atomic model
		
		decimal to binary
		>>> baseconvert(555,BASE10,BASE2)
		'1000101011'

		binary to decimal
		>>> baseconvert('1000101011',BASE2,BASE10)
		'555'

		integer interpreted as binary and converted to decimal (!)
		>>> baseconvert(1000101011,BASE2,BASE10)
		'555'

		base10 to base4
		>>> baseconvert(99,BASE10,"0123")
		'1203'

		base4 to base5 (with alphabetic digits)
		>>> baseconvert(1203,"0123","abcde")
		'dee'

		base5, alpha digits back to base 10
		>>> baseconvert('dee',"abcde",BASE10)
		'99'

		decimal to a base that uses A-Z0-9a-z for its digits
		>>> baseconvert(257938572394L,BASE10,BASE62)
		'E78Lxik'

		..convert back
		>>> baseconvert('E78Lxik',BASE62,BASE10)
		'257938572394'

		binary to a base with words for digits (the function cannot convert this back)
		>>> baseconvert('1101',BASE2,('Zero','One'))
		'OneOneZeroOne'
		
	'''

	###
	def __init__(self, fromdigits=('BASE10','BASE2'), todigits=('BASE10','BASE2')):
		""" Constructor.

			@fromdigits : Original base (BASE2, BASE10, BASE16, BASE62).
			@todigits : Final base (BASE2, BASE10, BASE16, BASE62).
			
		"""
		DomainBehavior.__init__(self)

		# Declaration des variables d'etat (actif tout de suite)
		self.state = {	'status':	'IDLE', 'sigma': INFINITY}

		# Local copy
		self.fromdigits = eval(fromdigits[0])
		self.todigits = eval(todigits[0])
		
		### msg dico
		self.msgDico = {}
		
	###
  	def intTransition(self):
		# Changement d'etat
		self.changeState()

	###
	def extTransition(self):
		
		# recuperation des messages sur les ports d'entree
		for i,port in enumerate(self.IPorts):
			msg = self.peek(port)
			if port != None:
				self.msgDico[i] = msg

		if self.msgDico != {}:
			# changement d'etat
			self.changeState('ACTIF',0)
		
	###
  	def outputFnc(self):
		assert(self.msgDico!={})
		
		for i in self.msgDico:
			msg = self.msgDico[i]
			msg.value[0] = baseconvert(msg.value[0],self.fromdigits, self.todigits)
			msg.time = self.timeNext
		
			# envoie des messages sur les ports de sortie
			self.poke(self.OPorts[i], msg)

		self.msgDico = {}
	###
  	def timeAdvance(self):
		return self.state['sigma']

	###
	def changeState( self, status = 'IDLE',sigma = INFINITY):
		self.state['status'] = status
		self.state['sigma'] = sigma

	def __str__(self):return "Gain"
