from shapely.geometry import Point
from shapely.geometry import Polygon

Point1 = Point(0.0,10.0)
Point2 = Point(10.0,0.0)

print "Abscice du point 1 : ", Point1.x
print "Abscice du point 2 : ", Point2.x


poly1 = Polygon([(3,3),(7,3),(7,7),(3,7)])
poly2 = Polygon([(6,3),(8,3),(8,9),(6,9)])

print "L'air du polygon 1 est : ", poly1.area

poly1Coupe = poly1.difference(poly2)

print "L'air du polygon 1 sans 2 est : ", poly1Coupe.area

polyUnion = poly1.union(poly2)

print "L'air du polygon 1 ou 2 est : ", polyUnion.area

polyIntersection = poly1.intersection(poly2)

print "L'air du polygon 1 et 2 est : ", polyIntersection.area

input()