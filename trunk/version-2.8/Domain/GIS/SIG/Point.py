# -*- coding: utf-8 -*-

"""
Name: Point.py
Brief description: Atomic Model which define a SIG place.
Author(s): L. Capocchi <capocchi@univ-corse.fr>
Version: 0.1
Last modified: 17/09/2010 
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS:
	- param: latitude, longitude, altitude, description, name, range, title, heading, folder
"""

### just for python 2.5
from __future__ import with_statement
from Domain.Myths.MythDomainBehavior import MythDomainBehavior 
from Domain.PowerSystem.Object import Message

# ===================================================================   #
class Point(MythDomainBehavior):
	""" Atomic Model which define a SIG place.
	"""

	###
	def __init__(self, latitude = 0.0, longitude = 0.0, altitude = 0.0, description = " ", name = " ", range = 6000, tilt = 45, heading = 0, folder = "folder"):
		""" Constructor.
			
			@param latitude : latitude
			@param longitude : longitude
			@param altditude : altitude
			@param description : description's point
			@param name : name's point
			@param range : range
			@param titl : title:
			@param heading : heading
			@param folder : name's folder
		"""
		MythDomainBehavior.__init__(self)

		self.lat = latitude
		self.lon = longitude
		self.alt = altitude
		self.desc = description
		self.name = name
		self.ran = range
		self.tilt = tilt
		self.head = heading
		self.folder = folder

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
	def __str__(self):return "SIGViewer"
