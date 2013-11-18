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
from Domain.Myths.Object import Message

# ===================================================================   #
class PointMyth(MythDomainBehavior):
	""" Atomic Model which define a SIG place.
	"""

	###
	def __init__(self, latitude = 0.0, longitude = 0.0, altitude = 0.0, description = " ", name = " ", range = 6000, tilt = 45, heading = 0, folder = "folder"):
		""" Constructor.
		"""
                
		MythDomainBehavior.__init__(self)
		#print "entrer point myth"

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
		self.state = {'status': 'INACTIF', 'sigma': INFINITY}
		#print "sortir point myth"
		
	###
	def outputFnc(self):
		"""
		"""
		# send output message
		#print "sortie point myth"
		self.poke(self.OPorts[0], Message([self,0,0], self.timeNext))

	###
	def extTransition(self):
		#print "entree ext trans point myth"
		
		self.state['status'] = 'ACTIF'
		self.state['sigma'] = 0

		#print "sortie ext trans point myth"
		
	def intTransition(self):
		#print "entree int trans point myth"
		self.state["status"] = 'IDLE'
		self.state["sigma"] = INFINITY
		#print "sorite int trans point myth"
					
	###
	def timeAdvance(self):
		#print "ta"
		return self.state['sigma']
	
	###
	def __str__(self):return "PointMyth"
