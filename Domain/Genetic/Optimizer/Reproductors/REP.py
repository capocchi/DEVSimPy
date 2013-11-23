#MODULES DEVS
from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from Domain.Genetic.Lib.CrossOver import CrossOverHalfAndHalf
from Domain.Genetic.Lib.CrossOver import CrossOverOneOfTwo

import random

class REP(SimpleAtomicModel):

#-----------------------------------------------------

    def __init__(self, mode="LOG"):
        SimpleAtomicModel.__init__(self)
        self.becomeDesactivate()
        self.mode = mode

#-----------------------------------------------------

    def extTransition(self):
        self.showScreen("RECEPTION DUNE POPULATION")
        self.population = self.readMessage()
        self.makeReproductionProcess()
        self.becomeActivate()

#-----------------------------------------------------

    def outputFnc(self):
        self.showScreen("ENVOIS DE LA NOUVELLE POPULATION")
        self.sendMessage(0,self.population)

#-----------------------------------------------------

    def intTransition(self):
        self.becomeDesactivate()

#-----------------------------------------------------

    def __str__(self):
        return "REP"

#-----------------------------------------------------

#GESTION DE LA FUSION

    def makeReproductionProcess(self):
        #Reproductors selection
        reproductors = filter(lambda individual: individual.reproductor, self.population.individuals)
        reproductors.reverse()
        
        #Children generation
        children = self.makeChildren(reproductors)

        #Chilrend integration
        self.population.integrateChildren(children)


    def makeChildren(self, parents):
        
        children =  []
        while len(children) < len(parents):
            parentA = random.choice(parents)
            parentB = random.choice(parents)
            if random.random() < 0.5:
                crossOver = CrossOverHalfAndHalf(parentA, parentB)
                children.append(crossOver.createChild())
            else:
                crossOver = CrossOverOneOfTwo(parentA, parentB)
                children.append(crossOver.createChild())
        return children