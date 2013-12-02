from Domain.Strategy.evaluator.abstractEvaluator import AbstractEvaluator
from Domain.Strategy.lib.ElevationRequest import ElevationRequest
from Domain.Strategy.lib.GIScompute import GIScompute

class ElevationEvaluator(AbstractEvaluator):

    def __init__(self, levelLimit=200.0):
        AbstractEvaluator.__init__(self)
        self.levelLimit = levelLimit
        self.precisionStep = 25 #Number Step
        self.precisionRange = 9 #Number of point for range circle
        self.myGIScompute = GIScompute()
        self.myElevationRequester = ElevationRequest()

    def getNextPlacement(self, evaluated, location, angle):
        beginLineLocation = location
        beginLineElevation = self.myElevationRequester.getElevationFromPoint(location)
        endLineLocation = self.myGIScompute.computeLatLngFromPointAndDistanceHandling(beginLineLocation, evaluated.maxInfluence, angle)
        lineElevations = self.myElevationRequester.getElevationFromLine(beginLineLocation, endLineLocation, self.precisionStep)
        lineSeize = self.myGIScompute.computeDistanceBetweenTwoPoint(beginLineLocation, endLineLocation)

        maxElevation = beginLineElevation + self.levelLimit
        minElevation = beginLineElevation - self.levelLimit
        counterStep = 0
        for elevation in lineElevations:
            if elevation > minElevation and elevation < maxElevation:
                counterStep += 1

        realDistance = counterStep * (lineSeize / self.precisionStep)

        return self.myGIScompute.computeLatLngFromPointAndDistanceHandling(beginLineLocation, realDistance, angle)


    def getRangePlacement(self, evaluated, location):
        unitAngle = 360 / self.precisionRange
        polygon = []

        for i in range(self.precisionRange):
            polygon.append(self.getNextPlacement(evaluated, location,i * unitAngle))

        return polygon

        

    def __str__(self):
            return "ElevationEvaluator"