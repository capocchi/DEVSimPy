from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from math import cos
from math import pi

class Inspyred_Problem(SimpleAtomicModel):

#--------------------Fonction initialisation------------------
    def __init__(self):
            SimpleAtomicModel.__init__(self)
    
#--------------------Fonction entree--------------------------
    def extTransition(self):
            #Recuperation d'une liste de solutions possibles et activation du calcul
            print "PROBLEM : RECEPTION POPULATION A EVALUER"
            self.population = self.readMessage()
            self.becomeActivate()
        
#--------------------Fonction sortie--------------------------    
    def outputFnc(self):
        #Transmistion de la liste des evaluations des solutions
        fitness = []
                
        for individualADN in self.population:
            fit = 10 * len(individualADN) + sum([((x - 1)**2 - 10 * cos(2 * pi * (x - 1))) for x in individualADN])
            fitness.append(fit)
    
        self.sendMessage(0, fitness)
        print "PROBLEM : TRANSMISSION DE LEVALUATION"

#--------------------Fonction interne-------------------------
    def intTransition(self):
        #Passage en mode attente d'autres demandes d'evaluation
        self.becomeDesactivate()
        
#--------------------Fonction ToString------------------------
    def __str__(self):
        return "Inspyred_Problem"
