# -*- coding: utf-8 -*-

"""
Name: Line.py
Brief description: Atomic Model which define a SIG line.
Author(s): L. Capocchi <capocchi@univ-corse.fr>, J.F. Santucci <santucci@univ-corse>, B. Poggi <poggi@univ-corse.fr>
Version: 0.1
Last modified: 08/07/2012
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS:
	- param: name, points, color, alpha
"""

### just for python 2.5
from __future__ import with_statement
from DomainInterface.DomainBehavior import DomainBehavior 
from Domain.Basic.Object import Message

import os

# ===================================================================   #
class Line(DomainBehavior):
	""" Atomic Model which define a SIG polygon.
	"""

	###
	def __init__(self, name = "", coords=[(0.00, 0.00, 0.00),(0.00, 0.00, 0.00)], bgcolor=("orange","lightblue"), typ = 'check', width=14.0, folder="", extendeddata = {'name': 'value'}):
		""" Constructor.
			
			@param name : polygon name
			@param coords : tuple of points (long, lat, alt)
			@param bgcolor : color of polygon
			@param typ : item check
			@param width : width of line
		"""
		
		DomainBehavior.__init__(self)

		### State variable
		self.state = {'status': 'INACTIF', 'sigma': 0}

		### local copy
		self.name = name
		self.coords = coords
		self.bgcolor = bgcolor[0]
		self.typ = typ
		self.width = width
		self.folder = folder
		self.extendeddata = extendeddata
		
	###
	def outputFnc(self):
		"""
		"""
		# send output message
		self.poke(self.OPorts[0], Message([self], self.timeNext))

	###
	def intTransition(self):
		self.state["status"] = 'IDLE'
		self.state["sigma"] = INFINITY
					
	###
	def timeAdvance(self):return self.state['sigma']
	
	###
	def __str__(self):return "Line"
