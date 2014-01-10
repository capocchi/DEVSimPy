# -*- coding: utf-8 -*-

"""
Name: Point.py
Brief description: Atomic Model which define a SIG point.
Author(s): L. Capocchi <capocchi@univ-corse.fr>, J.F. Santucci <santucci@univ-corse.fr>, B. Poggi <poggi@univ-corse.fr>
Version: 0.1
Last modified: 08/07/2012
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS:
	- param: latitude, longitude, altitude, description, name, icon_fileName, folder
"""

### just for python 2.5
from __future__ import with_statement
from DomainInterface.DomainBehavior import DomainBehavior 
from Domain.Basic.Object import Message
import os

# ===================================================================   #
class Point(DomainBehavior):
	""" Atomic Model which define a SIG point.
	"""

	###
	def __init__(self, latitude = 0.0, longitude = 0.0, altitude = 0.0, description = " ", name = " ", icon_fileName="", folder = "", extendeddata = {'name': 'value'}):
		""" Constructor.
			
			@param latitude : latitude data
			@param longitude : longitude data
			@param altditude : altitude data
			@param description : description of point which appear on the bottom of the icon
			@param name : name of point
			@param icon_fileName : image filename of point
			@param folder : name of folder
		"""
		DomainBehavior.__init__(self)
		
		self.lat = latitude
		self.lon = longitude
		self.alt = altitude
		self.desc = description
		self.name = name
		self.icon_fn = icon_fileName
		self.folder = folder
		self.extendeddata = extendeddata
		
		### State variable
		self.state = {'status': 'INACTIF', 'sigma': 0}
		
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
	def __str__(self):return "Point"
