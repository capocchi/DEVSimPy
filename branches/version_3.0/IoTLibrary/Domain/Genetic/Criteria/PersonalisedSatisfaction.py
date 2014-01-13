from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from Domain.Genetic.Lib.libSatisfaction import *

class PersonalisedSatisfaction(SimpleAtomicModel):
#--------------------Initialisation-------------------
    def __init__(self, optimalCurve=[(50,0),(100,1)]):
        SimpleAtomicModel.__init__(self)
        self.becomeDesactivate()
        self.optimalCurve = optimalCurve

#--------------------Fonction entree------------------
    def extTransition(self):
        self.inputValues = self.readMessage()
        self.listFitness = []
        for value in self.inputValues:
            self.listFitness.append(satisfactionCourbePerso(self.inputValue, self.optimalCurve))
        self.becomeActivate()

#--------------------Fonction sortie------------------
    def outputFnc(self):
        self.sendMessage(0, self.listFitness)
        

#--------------------Fonction interne------------------
    def intTransition(self):
        self.becomeDesactivate()

#--------------------Fonction ToString------------
    def __str__(self):
        return "PersonalisedSatisfaction"