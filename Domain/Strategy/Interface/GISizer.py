# -*- coding: utf-8 -*-

from DomainInterface.DomainBehavior import DomainBehavior
from Object import Message

from Domain.GIS.Point import Point
from Domain.GIS.Polygon import Polygon

class GISiser(DomainBehavior):

#INITIALISATION
	def __init__(self):
            DomainBehavior.__init__(self)
            self.state = {	'status': 'IDLE',
				'sigma':INFINITY,
                         }


#DEVS
	def extTransition(self):
            message = self.peek(self.IPorts[0])
            self.createPointAndPolygonList(message)

            self.state['sigma'] = 0
            

  	def outputFnc(self):
            message = Message()
            message.value = [self.listGISobject]
            message.time = self.timeNext
            self.poke(self.OPorts[0],message)


        def intTransition(self):
            self.state['sigma'] = INFINITY


  	def timeAdvance(self):
            return self.state['sigma']


#INTERNAL FUNCTION
        #Create list of GISobject to KMLize
        def createPointAndPolygonList(self,message):
            myData = message.value[0]

            self.listGISobject = []

            for evaluatedRepresentation in myData:
                self.listGISobject.append(self.convertToGISPoint(evaluatedRepresentation.point))
                self.listGISobject.append(self.convertToGISPolygon(evaluatedRepresentation.polygon))

        #Create a GIS::Point
        def convertToGISPoint(self, point):
            return Point(point[1],point[0])

        #Create a GIS::Polygon
        def convertToGISPolygon(self, polygon):
            return Polygon(polygon)