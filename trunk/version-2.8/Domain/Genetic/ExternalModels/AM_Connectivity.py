from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from pysal.weights import *
import csv

class AM_Connectivity(SimpleAtomicModel):

    def __init__(self, coverageRange=10, expectedNeighbor=2.0, minNeighbor=1, maxNeighbor=2, mode="LOG"):
        SimpleAtomicModel.__init__(self)
        
        #Parameters
        self.coverageRange = coverageRange
        self.expectedNeighbor = expectedNeighbor
        self.minNeighbor = minNeighbor
        self.maxNeighbor = maxNeighbor
        self.mode = mode
        
        self.becomeDesactivate()
        
        self.GENERATOR_UTILISE = "LOCATION"
        #self.GENERATOR_UTILISE = "BINARY AND TRANSLATOR"


    def extTransition(self):
        self.listStrategies = self.readMessage()
        
        #Adaptation sans model traduction precedent
        if self.GENERATOR_UTILISE == "LOCATION":
            conversion = []
            for indiv in self.listStrategies.individuals:
                i = indiv.ADN
                i = map(lambda x: (x.lat, x.lon, 20), i)
                conversion.append(i)
            self.listStrategies = conversion
        #------------------------------------------
        
        self.listAvgNeighborsFitness = []
        self.listMinNeighborsFitness = []
        self.listMaxNeighborsFitness = []
        self.listEcartsNeighborsFitness = []
        self.listgetTooMuchAndNotEnought = []
        self.listTotalNumberNeighbor = []
        self.listgetNumberNodeFalse = []
        
        for strategy in self.listStrategies:
            #Keep only x and y coordinates
            strategyWithoutRange = map((lambda x :(x[0],x[1],x[2])),strategy)
            
            #Compute neighborhood with pysal
            connectivity = DistanceBand(strategyWithoutRange, self.coverageRange)
            
            #Interpret neighborhood for each strategy
            self.listAvgNeighborsFitness.append(self.getAvgNumberNeighboor(connectivity))
            self.listMinNeighborsFitness.append(self.getMinNumberNeighboor(connectivity))
            self.listMaxNeighborsFitness.append(self.getMaxNumberNeighboor(connectivity))
            self.listEcartsNeighborsFitness.append(self.getEcartsNumberNeighboor(connectivity))
            self.listgetTooMuchAndNotEnought.append(self.getTooMuchAndNotEnought(connectivity))
            self.listTotalNumberNeighbor.append(self.getTotalNumberNeighbor(connectivity))
            self.listgetNumberNodeFalse.append(self.getNumberNodeFalse(connectivity))
            
        self.fitnessList = self.listAvgNeighborsFitness
        
        #Save CSV
        avgBest = self.listAvgNeighborsFitness[self.getIndexBestStrategy()]
        minBest = self.listMinNeighborsFitness[self.getIndexBestStrategy()]
        maxBest = self.listMaxNeighborsFitness[self.getIndexBestStrategy()]
        
        self.becomeActivate()
        
        self.showScreen(max(self.fitnessList))

    def outputFnc(self):
        self.sendMessage(0, self.fitnessList)


    def intTransition(self):
        self.becomeDesactivate()
        
        
    def __str__(self):
        return "AM_Connectivity"
        
    def getIndexBestStrategy(self):
        return self.fitnessList.index(max(self.fitnessList))
        
    def getBestStrategy(self):
        return self.listStrategies[self.getIndexBestStrategy()]
        
     
    def getNumberNodeFalse(self, connectivity):
        result = 0
        for listNodeNeighbors in connectivity.neighbors.values():
           if len(listNodeNeighbors) != self.expectedNeighbor:
               result -= 1
        return result
        
        
    def getTotalNumberNeighbor(self, connectivity):
        result = 0
        for listNodeNeighbors in connectivity.neighbors.values():
            result -= len(listNodeNeighbors)
        return result
        
        
    def getTooMuchAndNotEnought(self,connectivity):
        result = 0
        for listNodeNeighbors in connectivity.neighbors.values():
            numberNeighbors = len(listNodeNeighbors)
            if numberNeighbors > self.minNeighbor or numberNeighbors < self.minNeighbor:
                result -= 1
        return result
                

    def getEcartsNumberNeighboor(self,connectivity):
        result = 0
        for listNodeNeighbors in connectivity.neighbors.values():
            numberNeighbors = len(listNodeNeighbors)
            if numberNeighbors < self.expectedNeighbor:
                result -= (self.expectedNeighbor - numberNeighbors)
            elif numberNeighbors > self.expectedNeighbor:
                result -= (numberNeighbors - self.expectedNeighbor)
        return result
        
        
    def getAvgNumberNeighboor(self, connectivity):
        result = 0.0
        nb = 0
        for liste in connectivity.neighbors.values():
            result += len(liste)
            nb += 1
        result = float(result) / float(nb)
        return result
        
        
    def getMinNumberNeighboor(self, connectivity):
        result = None
        for liste in connectivity.neighbors.values():
            if result == None:
                result = len(liste)
            elif len(liste) < result:
                result = len(liste)            
        return result
        
        
    def getMaxNumberNeighboor(self, connectivity):
        maximum = 0
        for liste in connectivity.neighbors.values():
            if len(liste) > maximum:
                maximum = len(liste)   
        return maximum
            
        
        