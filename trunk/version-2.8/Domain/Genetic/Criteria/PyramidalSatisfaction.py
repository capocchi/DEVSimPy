from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from Domain.Genetic.Lib.libSatisfaction import *

class PyramidalSatisfaction(SimpleAtomicModel):
#--------------------Initialisation-------------------
    def __init__(self, optimalValue=float(50), ecartType=float(30), mode="LOG"):
        SimpleAtomicModel.__init__(self)
        self.becomeDesactivate()
        self.optimalValue = optimalValue
        self.ecartType = ecartType
        self.tolistValuesToEvaluate = []
        self.mode = mode

#--------------------Fonction entree------------------
    def extTransition(self):
        self.showScreen("RECEPTION DUNE DEMANDE DEVALUATION")
        #lecture de la valeur a evaluer
        self.listValuesToEvaluate = self.readMessage()
        self.becomeActivate()

#--------------------Fonction sortie------------------
    def outputFnc(self):
        listeSatisfaction = []
        for result in self.listValuesToEvaluate:
            listeSatisfaction.append(satisfactionPyramide(float(result),self.optimalValue,self.ecartType))
        self.showScreen("ENVOI DES SATISFACTIONS")
        self.sendMessage(0,listeSatisfaction)

#--------------------Fonction interne------------------
    def intTransition(self):
        self.becomeDesactivate()


#--------------------Fonction ToString------------
    def __str__(self):
        return "PyramidalSatisfaction"