# -*- coding: utf-8 -*-
from Domain.GIS.GISobject import GISobject
from Object import Message

class Polygon(GISobject):
        """
        This class model a geographical Line
        @author: Laurent CAPOCCHI
        @author: Bastien POGGI
        @organization: University Of Corsica
        @contact: capocchi@univ-corse.fr
        @contact: bpoggi@univ-corse.fr
        @since: 2010.03.28
        @version: 1.0
        """

#INITIALISATION
	def __init__(self,listCoordinates=[(0.0,0.0,0.0)], description = " ", name = " "):
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
            return "Polygon"