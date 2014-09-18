# -*- coding: utf-8 -*-
from Domain.GIS.GISobject import GISobject
from Object import Message

class Point(GISobject):
        """
        This class model a geographical Point
        @author: Laurent CAPOCCHI
        @author: Bastien POGGI
        @organization: University Of Corsica
        @contact: capocchi@univ-corse.fr
        @contact: bpoggi@univ-corse.fr
        @since: 2010.03.28
        @version: 1.0
        """

#INITIALISATION
	def __init__(self, latitude=1.0, longitude=1.0, elevation=0.0, name=" ", description=" "):
		""" Constructor.
                        @param latitude : the point altitude
                        @param longitude : the point longitude
                        @param elevation : the point elevation
			@param description : description's point
			@param name : name's point
		"""
                GISobject.__init__(self)

                self.coordinate = (latitude,longitude,elevation)
		self.name = name
                self.desc = description

		self.state = {'status': 'INACTIF', 'sigma': 0}


#INTERNAL FUNCTION
        def __str__(self):
            return "Point"

