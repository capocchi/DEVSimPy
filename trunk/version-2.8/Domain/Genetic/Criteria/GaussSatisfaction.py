from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from Domain.Genetic.Lib.libSatisfaction import *

class GaussSatisfaction(SimpleAtomicModel):
#--------------------Initialisation-------------------
    def __init__(self, optimalValue=0, ecartType=0):
        SimpleAtomicModel.__init__(self)
        self.state = {'sigma' : INFINITY}
        self.optimalValue = optimalValue
        self.ecartType = ecartType

#--------------------Fonction entree------------------
    def extTransition(self):
        #lecture de la valeur a evaluer
        self.inputValue = self.readMessage()
        self.state = {'sigma' : 0}

#--------------------Fonction sortie------------------
    def outputFnc(self):
        #calcul de l'evaluation
        satisfaction = satisfactionGaussNormalisee(self.inputValue, self.optimalValue, self.ecartType)
        self.sendMessage(0, satisfaction)

#--------------------Fonction interne------------------
    def intTransition(self):
        self.state['sigma'] = INFINITY

#--------------------Fonction TA------------------
    def timeAdvance(self):
        return self.state['sigma']

#--------------------Fonction ToString------------
    def __str__(self):
        return "GaussSatisfaction"