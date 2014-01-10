#MODULES DEVS
from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel

class AMSelector(SimpleAtomicModel):
    """
    This class select the half best individuals
    @author: Bastien POGGI
    @organization: University Of Corsica
    @contact: bpoggi@univ-corse.fr
    @since: 2012.03.29
    @version: 1.0
    """

#-----------------------------------------------------

    def __init__(self,mode="LOG"):
        SimpleAtomicModel.__init__(self)
        self.mode = mode
        self.becomeDesactivate()

#-----------------------------------------------------

    def extTransition(self):
        self.showScreen("RECEPTION DUNE POPULATION")
        self.population = self.readMessage()

        self.showScreen("TRI DES INDIVIDUS")
        self.population.clearSelection()
        self.population.sortPopulation()

        #SELECTIONNE LA MOITIER DES MEILLEURES COMME REPRODUCTEUR
        self.numberReproductor = 0
        for i in range(len(self.population.individuals)/2, len(self.population.individuals)):
            self.population.individuals[i].becomeReproductor()
            self.numberReproductor += 1
            
        self.becomeActivate()

#-----------------------------------------------------

    def outputFnc(self):
        self.showScreen("ENVOIS DE LA POPULATION COMPOSEE DE" + str(self.numberReproductor) + "REPRODUCTEUR")
        self.sendMessage(0,self.population)

#-----------------------------------------------------

    def intTransition(self):
        self.becomeDesactivate()

#-----------------------------------------------------

    def __str__(self):
        return "AMSelector"
