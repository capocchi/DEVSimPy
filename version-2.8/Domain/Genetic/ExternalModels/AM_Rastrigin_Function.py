from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from pysal.weights import *
import math

class AM_Connectivity(SimpleAtomicModel):

    def __init__(self, nbDimension=1): #LA FONCTION DEVRA ETRE MODIFIE POUR PRENDRE ETRE UTILISEE EN PLUSIEUR DIMENSIONS
        SimpleAtomicModel.__init__(self)
        #self.state = {'sigma' : INFINITY} #NORMAL MODE
        self.state = {'sigma' : 0} #DEBUG MODE
        #self.receiveValue = [] #NORMAL MODE
        self.receiveValue = [1, 1, 1 ,0] #DEBUG MODE
        
#--------------------Fonction entree------------------
    def extTransition(self):
        print "RASTRIGIN : RECEPTION DEMANDE EVALUATION"
        #LECTURE DU MESSAGE
        self.receiveValue = self.readMessage()
        
#--------------------Fonction sortie------------------     
    def outputFnc(self):
        print "RASTRIGIN : CALCUL ET ENVOI DU RESULTAT DE LA FONCTION"
        
        #INTERPRETATION BINAIRE #UTILISER PYTHON UTILITIES A LA PLACE
        puissance = 2 ** len(self.receiveValue)
        x = 0
        
        for bit in chaineBinaire:
            if bit == 1:
                x += puissance
            puissance = puissance / 2
        
        print chaineBinaire, " --- DECIMAL --->", x
        result = 10 + x ** 2 - 10 * math.cos(2 * math.pi * x)
        self.sendMessage(0,result)
        
        
    def intTransition(self):
        print "RASTRIGIN : MISE EN ATTENTE DUNE AUTRE DEMANDE DEVALUATION"
        self.state['sigma'] = INFINITY

#--------------------Fonction TA------------------
    def timeAdvance(self):
        return self.state['sigma']

#--------------------Fonction ToString------------
    def __str__(self):
        return "AM_Rastrigin_Function"
        