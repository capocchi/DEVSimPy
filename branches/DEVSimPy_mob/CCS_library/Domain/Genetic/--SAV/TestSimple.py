from shapely.geometry import Polygon
from shapely.geometry import Point
from random import Random
import inspyred
import time

class Deploiement(inspyred.benchmarks.Benchmark):
    
    def __init__(self):
        pass

    def generator(self, random, args):
        taille = 2
        individu = []
        for i in range(taille):
            individu.append(Random().randint(0,10))
        print "GENERATEUR" , individu
        return individu
        
    def evaluator(self, candidates, args):
        print "EVALUATEUR"
        fitness = []
        objectif = 10
        for candidate in candidates:
            if sum(candidate)>objectif:
                fitness.append(sum(candidate)-objectif)
                print candidate, "note :", sum(candidate)-objectif
            else:
                fitness.append(objectif-sum(candidate))
                print candidate, "note :", objectif-sum(candidate)

        return fitness
    
    def terminator(self, population, num_generations, num_evaluations, args):
        print "TERMINATEUR"
        if max(population).fitness < 0.2:
            return True
        else:
            return False
    

            
        
problem = Deploiement()
ea = inspyred.ec.ES(Random())
ea.terminator = problem.terminator
final_pop = ea.evolve(generator=problem.generator, 
                      evaluator=problem.evaluator, 
                      pop_size=3, 
                      maximize=False)

final_pop.sort(reverse=True)
print final_pop[0].candidate
