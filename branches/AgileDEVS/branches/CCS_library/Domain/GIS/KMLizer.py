# -*- coding: utf-8 -*-

from DomainInterface.DomainBehavior import DomainBehavior
from GIS.lib.KML import KMLcreator
import os.path

class KMLizer(DomainBehavior):
        """
        This class model a genetor of KML output with geographical object
        @author: Laurent CAPOCCHI
        @author: Bastien POGGI
        @organization: University Of Corsica
        @contact: capocchi@univ-corse.fr
        @contact: bpoggi@univ-corse.fr
        @since: 2010.04.07
        @version: 1.0
        """

#INITIALISATION
	def __init__(self, fileName = os.path.join(os.getcwd(), "SortieKML")):
            """ Constructor.
            @param fileName : output file
            """
            DomainBehavior.__init__(self)
            
            ### local copy
            self.fileName = fileName
            
            self.state = {'sigma': INFINITY}
            self.myKML = KMLcreator(fileName + ".kml")

#DEVS
        def extTransition(self):
            for receivePort in self.IPorts:
                message = self.peek(receivePort)
                if message != None :
                    self.addGISObjectToKML(message.value[0]) #Add the geographical object to KML Tree
            self.state['sigma'] = 0


  	def intTransition(self):
            print "transition interne"
            self.myKML.save()
            print "Sauvegarde Effectuee"
            self.state['sigma'] = INFINITY


  	def timeAdvance(self):
		return self.state['sigma']


#INTERNAL FUNCTION
	def __str__(self):
            return "KMLizer"


        def addGISObjectToKML(self,GISobject):
            #ONE OBJECT
            if GISobject.__class__.__name__ == 'Polygon':
                self.myKML.addPolygon(GISobject.name,GISobject.desc,GISobject.listCoordinates)

            elif GISobject.__class__.__name__ == 'Line':
                self.myKML.addLine(GISobject.name,GISobject.desc,GISobject.listCoordinates)

            elif GISobject.__class__.__name__ == 'Point':
                self.myKML.addPlaceMark(GISobject.name,GISobject.desc,GISobject.coordinate)

            else:
                #COLLECTION OBJECT
                if len(GISobject) > 1:
                    for theGISobject in GISobject:

                        if theGISobject.__class__.__name__ == 'Point':
                            self.myKML.addPlaceMark("point","",theGISobject.coordinate)

#                        elif theGISobject.__class__.__name__ == 'Line':
#                            self.myKML.addLine("line","",theGISobject.listCoordinates)
#
                        elif theGISobject.__class__.__name__ == 'Polygon':
                            print "creation polygon"
                            self.myKML.addPolygon("name","description",theGISobject.listCoordinates)
                else:
                    print "Unknow object conneted"

