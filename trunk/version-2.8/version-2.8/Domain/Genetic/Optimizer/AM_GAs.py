from Domain.Genetic2.Tools.SimpleAtomicModel import SimpleAtomicModel

import random
#from random import Random
from time import time
import inspyred

#FUNCTION GA
def fitness(self):
    return self.simulationResult
    
def generator():
    #RENVOIS LA POPULATION EN COURS DE LA STRATEGIE DONT IL EST ISSU
    populationNumber = 5
    population = []
    
    positionsNumber = 15
    for i in range(populationNumber):
        strategy = []
        for j in range(positionsNumber):
            x = random.random()*100
            y = random.random()*100
            strategy.append((x,y))
        population.append(strategy)

    return population
        

def variator(self):
    pass


class AM_GAs(SimpleAtomicModel):
    
    def __init__(self, populationSeize=100, maxIteration=1000, maximize=True, num_elites=1):
        
        SimpleAtomicModel.__init__(self)
        self.state = {'sigma' : 0}
        self.state['action'] = "GENESE"
        
        #CONFIGURATION
        #self.populationSeize = populationSeize
        #self.maxIteration = 1000
        #self.maximize = True
        #self.num_elites = num_elites
        #
        #NEED EVOLVE
        #self.simulationResult = []
        #self.currentPopulation = []
        #
        #PARAMETER
        #self.generator = generator
        #self.evaluator = fitness
        #self.termination = None
        #self.variator = None
        #
        #self.randomizer = Random()
        #self.randomizer.seed(time())
        
    def extTransition(self): #RECEIPT SIMULATION RESULT
        print "GAs : RESULTATS RECUS"
        self.simulationResult =  self.readMessage()
        print self.simulationResult
          
    def outputFnc(self):
        #if self.state['action']=="OPTIMIZE":
        #    myAG = inspyred.ec.GA(self.randomizer)
        #    #REGARDER LE TYPE DE NEWPOPULATION
        #    newPopulation = ea.evolve(generator = self.generator,
        #                              evaluator = self.evaluator,
        #                              pop_size = self.populationSeize,
        #                              maximize = self.maximize,
        #                              max_evaluations = self.maxIteration,
        #                              num_elites = self.num_elites)
        #    #MEMORISATION DE LA POPULATION ENVOYEE
        #    self.sendMessage(0,self.populationSend)
        #    self.populationSend = newPopulation.population
        #
        if self.state['action']=="GENESE":
            print "GAs : GENERATION POPULATION INITIALE"
            strategies = generator()
            print "GAs : ENVOI DE LA POPULATION"
            self.sendMessage(0,strategies)
            self.currendPopulation = strategies
            
            
        
    def intTransition(self):
        if self.state['action'] == "GENESE":
            print "GAs : CHANGEMENT ETAT : GENESE --> OPTIMIZE "
            self.state['action'] = "OPTIMIZE"