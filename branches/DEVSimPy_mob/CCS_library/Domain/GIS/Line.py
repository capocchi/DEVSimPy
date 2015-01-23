# -*- coding: utf-8 -*-

"""
Name: Line.py
Brief description: 
Author(s): B. Poggi <bpoggi@univ-corse.fr>, L. Capocchi <capocchi@univ-corse.fr>
Version: 0.1
Last modified: 28/03/2011 
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS:
"""

from Domain.GIS.GISobject import GISobject

class Line(GISobject):


#INITIALISATION
	def __init__(self, listCoordinates=[(42.305721,9.150281,0),(42.292485,9.131184,0),(42.291691,9.164314,0)], name = " ", description = " "):
		""" Constructor.
			@param listCoordinate : list of coordinates of type (longitude,latitude,elevation)
			@param description : description's point
			@param name : name's point
		"""
		GISobject.__init__(self)

		self.listCoordinates = listCoordinates
		self.name = name
		self.desc = description

		self.state = {'status': 'INACTIF', 'sigma': 0}


#INTERNAL FUNCTION
	def __str__(self):
		return "Line"