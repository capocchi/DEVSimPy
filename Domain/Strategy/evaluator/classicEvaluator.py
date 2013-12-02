from Domain.Strategy.evaluator.abstractEvaluator import AbstractEvaluator
from Domain.Strategy.lib.GIScompute import GIScompute

class ClassicEvaluator(AbstractEvaluator):

    precision = 10

    def __init__(self):
        AbstractEvaluator.__init__(self)


    def getNextPlacement(self, evaluated, location, angle):
        myGIScompute = GIScompute()
        return myGIScompute.computeLatLngFromPointAndDistanceHandling(location, evaluated.maxInfluence, angle)


    def getRangePlacement(self, evaluated, location):
        precision = 10
        polygon = []
        myGIScompute = GIScompute()
        
        for i in range(precision):
            angle = i * (360 / precision)
            polygon.append(myGIScompute.computeLatLngFromPointAndDistanceHandling(location, evaluated.maxInfluence, angle))

#        print "ClassicEvaluator :: ", polygon
        return polygon


    def __str__(self):
            return "ClassicEvaluator"