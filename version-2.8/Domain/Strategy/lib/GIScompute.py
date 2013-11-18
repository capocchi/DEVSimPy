import math

class GIScompute:

    def __init__(self,R=6378137):
        self.R = R

    def computeDistanceBetweenTwoPoint(self,pointA,pointB):
        lat1 = pointA[0]
        lat2 = pointB[0]
        lon1 = pointA[1]
        lon2 = pointB[1]

        dLat = math.radians(lat2-lat1)
        dLon = math.radians(lon2-lon1)
        a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = self.R * c
        return d



    def computeHandlingBetweenTwoPoint(self,PointA,PointB):
        lat1 = math.radians(PointA[0])
        lat2 = math.radians(PointB[0])
        lon1 = math.radians(PointA[1])
        lon2 = math.radians(PointB[1])

        y = -math.sin(lon1-lon2) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon1-lon2)
        brng = math.degrees(math.atan2(y, x))
        return brng



    def computeLatLngFromPointAndDistanceHandling(self,Point,distance,handling):
        lat1 = math.radians(Point[0])
        lon1 = math.radians(Point[1])
        brng = math.radians(handling)

        d = distance/10
        R = 637813.7

        lat2 = math.asin( (math.sin(lat1)* math.cos(d/R) ) + ( math.cos(lat1) * math.sin(d/R) * math.cos(brng) ) )
        lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(d/R)* math.cos(lat1),math.cos(d/R)-math.sin(lat1)*math.sin(lat2))

        return (math.degrees(lat2),math.degrees(lon2))

#--------------------TEST---------------------#

#myGIScompute = GIScompute()
#print myGIScompute.computeDistanceBetweenTwoPoint((12,12),(13,13))
#print myGIScompute.computeHandlingBetweenTwoPoint((12,03),(24,02))
#print myGIScompute.computeLatLngFromPointAndDistanceHandling((7,4),150,45)