import chilkat

class KMLcreator:

    def __init__(self,fileName="map.kml"):
        self.fileName = fileName
        self.myKML = chilkat.CkXml()
        self.myKML.put_Tag('kml')
        self.myKML.AddAttribute("xmlns","http://www.opengis.net/kml/2.2")
        self.myKML = self.myKML.NewChild("Document","")


    def addPlaceMark(self,name,description,coordinates):
        coordinates = ("%f,%f,%f")%(coordinates[0],coordinates[1],coordinates[2])

        myPlacemark = chilkat.CkXml()
        myPlacemark.put_Tag("Placemark")
        myPlacemark.NewChild2("name",name)
        myPlacemark.NewChild2("description",description)

        myPoint = chilkat.CkXml()
        myPoint.put_Tag("Point")
        myPoint.NewChild2("coordinates",coordinates)

        myPlacemark.AddChildTree(myPoint)

        self.myKML.AddChildTree(myPlacemark)


    def addLine(self,name,description,listCoordinates,visibility="1",tessellate="1",altitudeMode="clampToGround"):

        myPlacemark = chilkat.CkXml()
        myPlacemark.put_Tag("Placemark")
        myPlacemark.NewChild2("name",name)
        myPlacemark.NewChild2("visibility",visibility)
        myPlacemark.NewChild2("description",description)

        myLine = chilkat.CkXml()
        myLine.put_Tag("LineString")
        myLine.NewChild2("tessellate",tessellate)
        myLine.NewChild2("altitudeMode",altitudeMode)
        myLine.NewChild2("coordinates",self.listCoordinatesToStringLine(listCoordinates))

        myPlacemark.AddChildTree(myLine)

        self.myKML.AddChildTree(myPlacemark)


    def addPolygon(self,name,description,outerListCoordinates,color="7d0000ff",lineWidth="2",innerListCoordinates=[],extrude="1",altitudeMode="clampToGround"):
        myPlacemark = chilkat.CkXml()
        myPlacemark.put_Tag("Placemark")
        myPlacemark.NewChild2("name",name)
        myPlacemark.NewChild2("description",description)

        myStyle = myPlacemark.NewChild("Style","")
        myLineStyle = myStyle.NewChild("LineStyle","").NewChild2("width",lineWidth)
        myPolyStyle = myStyle.NewChild("PolyStyle","").NewChild2("color",color)

        myPolygon = chilkat.CkXml()
        myPolygon.put_Tag("Polygon")
        myPolygon.NewChild2("extrude",extrude)
        myPolygon.NewChild2("altitudeMode",altitudeMode)

        outerBoundary = myPolygon.NewChild("outerBoundaryIs","")
        LinearRing = outerBoundary.NewChild("LinearRing","")
        LinearRing.NewChild2("coordinates",self.listCoordinatesToStringLine(outerListCoordinates))

        if innerListCoordinates != []:
            innerBoundary = myPolygon.NewChild("innerBoundaryIs","")
            LinearRing = innerBoundary.NewChild("LinearRing","")
            LinearRing.NewChild2("coordinates",self.listCoordinatesToStringLine(innerListCoordinates))

        myPlacemark.AddChildTree(myPolygon)

        self.myKML.AddChildTree(myPlacemark)


    def save(self):
        self.myKML.SaveXml(self.fileName)

    #INTERNAL FUNCTIONS

#    def listCoordinatesToStringLine(self,listCoordinates):
#        result = "\n \t \t \t"
#        if listCoordinates != None:
#            for coordinate in listCoordinates:
#                result += coordinate
#                result += "\n \t \t \t"
#        return result

    def listCoordinatesToStringLine(self,listCoordinates):
        result = "\n \t \t \t"
        if listCoordinates != None:
                myVar = map(lambda a: "%f,%f"%(a[1],a[0]),listCoordinates) #2D
#                myVar = map(lambda a: "%f,%f,%f"%(a[0],a[1],a[2]),listCoordinates) #3D
                for v in myVar:
                    result += v
                    result += "\n \t \t \t"
        return result

#monCreateur = KMLcreator()
#
#monCreateur.addPlaceMark("Mon Point 1","Premier point en KML",(12,12,0))
#monCreateur.addPlaceMark("Mon Point 2","Deuxieme point en KML",(13,13,0))
#
#monCreateur.addLine("Ma ligne","Premier ligne en KML",[(13,13,0),(12,12,0),(20,20,0),(40,40,0)])
#
#monCreateur.addPolygon("monCarre","cest un carre",[(13,13,0),(13,12,0),(12,12,0),(12,13,0),(13,13,0)])
#
#monCreateur.save()

