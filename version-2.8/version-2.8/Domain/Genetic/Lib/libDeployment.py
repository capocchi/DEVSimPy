#SHAPELY
from shapely.geometry import Polygon
from shapely.geometry import Point

#VIZUALISATION
from matplotlib import pyplot
from descartes import PolygonPatch
import matplotlib.image as mpimg

#TEST
import random

#---------------------------------------------------------------------------------------------
#                                       NORMAL VERSION
#---------------------------------------------------------------------------------------------
class CoverageCalculator:
    
    def __init__(self, listCoordinatesDeploymentAreas, listAttenuationAreas, listCoordinatesDeployedObjects):
        self.listCoordinatesDeploymentAreas = listCoordinatesDeploymentAreas
        self.listAttenuationAreas = listAttenuationAreas
        self.listCoordinatesDeployedObjects = listCoordinatesDeployedObjects
        self.deploymentAreas = []
        self.deploymentArea = Polygon()
        self.circles = []
        self.coveredArea = Polygon()
        self.uncoveredArea = Polygon()

#        print listCoordinatesDeployedObjects

        for i in range(len(listCoordinatesDeploymentAreas)):
            self.deploymentAreas.append(DeploymentArea(listCoordinatesDeploymentAreas[i], self.listAttenuationAreas[i], self.listCoordinatesDeployedObjects))

        for area in self.deploymentAreas:
            self.deploymentArea = self.deploymentArea.union(area.shapelyMe)

        for deploymentArea in self.deploymentAreas:
            self.circles = self.circles + deploymentArea.myNode

#        print "IL Y A", len(self.circles), "OJETS DEPLOYES"

        #CALCUL SURFACE COUVERTE
        for cercle in self.circles:
            self.coveredArea = self.coveredArea.union(cercle)
        self.coveredArea = self.coveredArea.intersection(self.deploymentArea)
        
        #CALCUL SURFACE NON COUVERTE
        self.uncoveredArea = self.deploymentArea.difference(self.coveredArea)
        
        #CALCUL DES TAUX
        self.coverateRate = self.coveredArea.area * 100 / self.deploymentArea.area
        self.uncoveredRate = self.uncoveredArea.area * 100 / self.deploymentArea.area

    def show_Resume(self):
        print "Le taux de couverture est de", self.coverateRate
        print "Le taux de non couverture est de", self.uncoveredRate
        print "La taille de la zone est", self.deploymentArea.area
        print "\tDivisee en zones de taille:"
        for zone in self.deploymentAreas:
            print '\t',zone.shapelyMe.area
        print "La taille de la zone couverte est", self.coveredArea.area
        print "La taille de la zone non couverte est", self.uncoveredArea.area
        
class DeploymentArea:

    def __init__(self, coordinates, attenuation, listPoint):
        self.shapelyMe = Polygon(coordinates)
        self.attenuation = attenuation

        #trouver la zone de point et attribuer la portee correspondante
        self.myNode = []
        for point in listPoint:
            if self.shapelyMe.contains(Point(point[0],point[1])) or self.shapelyMe.touches(Point(point[0],point[1])):
                self.myNode.append(Point(point[0],point[1]).buffer(point[2]*self.attenuation))
                del point

        self.coveredArea = Polygon()
        for node in self.myNode:
            self.coveredArea = self.coveredArea.union(node)
            
#---------------------------------------------------------------------------------------------
#                                       FAST VERSION
#---------------------------------------------------------------------------------------------
        
class FastCoverageCalculator:
    
    def __init__(self, listCoordinatesDeploymentAreas, listAttenuationAreas, listCoordinatesDeployedObjects):

        self.area = Polygon()
        self.coveredArea = Polygon()
        self.repartition = [] #Node in each subarea

        for i in range(len(listCoordinatesDeploymentAreas)):
            subArea = (FastDeploymentArea(listCoordinatesDeploymentAreas[i],
                       listAttenuationAreas[i], 
                       listCoordinatesDeployedObjects))
            self.repartition.append(subArea.numberNode)
                       
            self.area = self.area.union(subArea.area)
            self.coveredArea = self.coveredArea.union(subArea.coverArea)
        
        self.coveredArea = self.coveredArea.intersection(self.area)
        self.coverateRate = self.coveredArea.area * 100 / self.area.area
        
class FastDeploymentArea:
    def __init__(self, coordinates, attenuation, listPoint):
        self.area = Polygon(coordinates)
        self.coverArea = Polygon()
        self.numberNode = 0

        for point in listPoint:
            if self.isMine(point):
                self.addPoint(point,attenuation)
                self.numberNode += 1

    def isMine(self, point):
        return self.area.contains(Point(point[0],point[1])) or self.area.touches(Point(point[0],point[1]))
        
    def addPoint(self,point,attenuation):
        self.coverArea = self.coverArea.union(Point(point[0],point[1]).buffer(point[2]*attenuation))
        del point

#---------------------------------------------------------------------------------------------
#                                       VIZUALISATION
#---------------------------------------------------------------------------------------------    
        
class CoverageVizualisation:
    
    def __init__(self, coverageCalculator):
        self.coverageCalculator = coverageCalculator

        self.windows = pyplot.figure()
        self.representation = self.windows.add_subplot(1, 1, 1)

        self.representation.set_title('Deployment')
        self.representation.set_xlim(0,100)
        self.representation.set_ylim(0,100)
        self.representation.set_xticks(range(0,100,10))
        self.representation.set_yticks(range(0,100,10))
        self.representation.text(10,10,"COVERAGE : "+str(self.coverageCalculator.coverateRate),size=20)
        self.representation.set_aspect(1)
        self.representation.grid()
        self.representation.set_autoscalex_on(True)
        self.representation.set_autoscaley_on(True)

        self.vizualise()
        
    def vizualise(self):
        self.drawPolygons(self.getPoints(), "#FF6A58", "#000000", 1)
        pyplot.show()

    def drawPolygons(self, listPolygons, color1, color2, order):
        for polygon in listPolygons:
            drawedPolygon = PolygonPatch(polygon, fc=color1, ec=color2, alpha=0.80, zorder=order)
            self.representation.add_patch(drawedPolygon)

    def getPoints(self):
        return self.coverageCalculator.circles

    def getArea(self,num):
        return [self.coverageCalculator.deploymentAreas[num].shapelyMe]

