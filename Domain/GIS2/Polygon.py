# -*- coding: utf-8 -*-

"""
Name: Polygon.py
Brief description: Atomic Model which define a SIG polygon.
Author(s): L. Capocchi <capocchi@univ-corse.fr>, J.F. Santucci <santucci@univ-corse>
Version: 0.1
Last modified: 08/07/2012
GENERAL NOTES AND REMARKS: 
GLOBAL VARIABLES AND FUNCTIONS:
	- param: name, points, color, alpha
"""

### just for python 2.5
from __future__ import with_statement
#from DomainInterface.DomainBehavior import DomainBehavior 
#from Domain.Basic.Object import Message
from Domain.GIS2.Line import Line

import os

# ===================================================================   #
class Polygon(Line):
	""" Atomic Model which define a SIG polygon.
	"""

	###
	def __init__(self, name="", coords=[(0.00, 0.00, 0.00),(0.00, 0.00, 0.00)], bgcolor=("orange","lightblue"), alpha=77, relativeground=False, folder="", extendeddata = {'name': 'value'}):
		""" Constructor
			
			@param name : name of polygon
			@param coords : tuple of points (long, lat, alt)
			@param bgcolor : color of polygon
			@param alpha : alpha filter
			@param relativeground: relative ground param
			@param folder : name of folder
			@param extendeddata : extended data
		"""

		#DomainBehavior.__init__(self)
		Line.__init__(self, name =name, coords = coords+[coords[0]], bgcolor = bgcolor, folder=folder, extendeddata = extendeddata)

		self.alpha = alpha
		self.relativeground = relativeground
	
	def extTransition(self):
		"""
		"""
		### if it receive dico with new GIS values, we update them and output new value for google earth update
		for port, msg in self.peek_all():
			elem = msg.value[0]
			for k, v in elem.items():
				if hasattr(self, str(k)):
					setattr(self, str(k), v)

		self.state = {'status': 'INACTIF', 'sigma': 0}

	###
	def __str__(self):return "Polygon"