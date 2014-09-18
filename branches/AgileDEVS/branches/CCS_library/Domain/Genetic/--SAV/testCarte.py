#CARTE 100 * 100
#PORTE capteur 5 metres

from shapely.geometry import *
portee = 5

carte = Polygon([(0,0), (0,100), (100,100), (100,0)])

capteur1 = Point(70,50).buffer(portee)
capteur2 = Point(50,50).buffer(portee)
capteur3 = Point(60,50).buffer(portee)

zone = capteur1.union(capteur2)
zone = zone.union(capteur3)

print zone.area
print carte.area
input()