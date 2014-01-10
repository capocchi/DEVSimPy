from inspyred.benchmarks import Benchmark
from shapely.geometry import Polygon
from shapely.geometry import Point
import random

from time import time
from random import Random
import inspyred

class Deploiement(Benchmark):
    
    def __init__(self, minX, maxX, minY, maxY):
        self.minX = minX
        self.maxX = maxX
        self.minY = minY
        self.maxY = maxY
        self.AoD = [(minX,minY),(minX,maxY),(maxX,maxY),(maxX,minY)]
        self.coverageRange = 10
    
    
    def generator(self, random, args):
        numberPoints = args.get('numberPoints',2) #DONC *2
        print numberPoints
        strategy = []
        for i in range(numberPoints):
            
            point = random.randint(self.minX,self.maxX)
            strategy.append(point)
            
            point = random.randint(self.minY,self.maxY)
            strategy.append(point)
            
        print 'les points sont : ', strategy
        return strategy
            
    def evaluator(self, candidates, args):
        fitness = []
        for candidate in candidates:
            fitness.append(self.evaluateStrategy(candidate))
        return fitness
    
    def evaluateStrategy(self, strategy):
        #CONVERTION
        strategy = self.convertListToListTuple(strategy)
        uncoveredPolygon = Polygon(self.AoD)
        for point in strategy:
            coverageZone = Point(point[0],point[1]).buffer(self.coverageRange)
            uncoveredPolygon = uncoveredPolygon.difference(coverageZone)
        coveredPolygon = Polygon(self.AoD).difference(uncoveredPolygon)
        return coveredPolygon.area * 100 / (Polygon(self.AoD).area)
        
    def convertListToListTuple(self,list1):
        resu = []
        for i in range(0,len(list1),2):
            resu.append((list1[i],list1[i+1]))
        return resu
            
        
prng = Random()
prng.seed(time()) 
        
problem = Deploiement(0,100,0,100)
ea = inspyred.ec.ES(prng)
final_pop = ea.evolve(generator=problem.generator, 
                        evaluator=problem.evaluator, 
                        pop_size=2, 
                        max_evaluations=100,
                        maximize=True)

best = max(final_pop)
print('Best Solution: \n{0}'.format(str(best)))