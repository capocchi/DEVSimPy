from shapely.geometry import *

class Deploiement:

    def __init__(self, lenght, weight, sensorRange, deploiement):
        areaDep = Polygon( [ (0,0) , (lenght,0) , (lenght,weight) , (0, weight) ] )
        areaCover = Polygon( [ (0,0) ,(0,0) ,(0,0) , (0,0) ] )

        for coordinate in deploiement:
            x = coordinate[0]
            y = coordinate[1]
            coverageRange = Point(x, y).buffer(sensorRange)
            print coverageRange.area
            areaCover = areaCover.union(coverageRange)

        areaCover = areaCover.intersection(areaDep) #SUPRESSION DES DEBORDEMENTS

        print "la surage de la zone est", areaDep.area
        print "la surface de couverture est", areaCover.area
            

deploiementCoordonnees = [ (0,1) , (5,4), (8,2), (3,3), (4,5), (2,0) ]

D = Deploiement(10, 10, 2, deploiementCoordonnees)
