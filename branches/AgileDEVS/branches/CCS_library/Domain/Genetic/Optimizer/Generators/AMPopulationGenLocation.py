#MODULE AGs
from Domain.Genetic.Lib.Gene import GeneLocationFactory
from Domain.Genetic.Lib.Individual import IndividualFactory
from Domain.Genetic.Lib.Population import PopulationFactory

#MODULES DEVS
from DomainInterface.DomainBehavior import DomainBehavior
from Domain.Basic.Object import Message

class AMPopulationGenLocation(DomainBehavior):
    """
    This class build a population composed of individual composed themself of Genes type: Location
    @author: Bastien POGGI
    @organization: University Of Corsica
    @contact: bpoggi@univ-corse.fr
    @since: 2012.03.29
    @version: 1.0
    """


    def __init__(self, populationSize=10 ,ADNSize=5, univers=[(0,0),(100,0),(100,100),(0,100)]):
        """
        @param populationSize:
        @param ADNSize:
        @param univers:
        """
        DomainBehavior.__init__(self)
        self.populationSize = populationSize
        self.ADNSize = ADNSize
        self.univers = univers
        #Lancement de lagorithme genetique
        self.state = {'sigma' : 0}
        
    def outputFnc(self):
        #instansiation gen factory (genes possibles)
        geneF = GeneLocationFactory(self.univers)
        
        #instansiation de l'individu (une liste de genes possibles)
        individualF = IndividualFactory(self.ADNSize, geneF)
        
        #instansiation de la population (une liste dindividus)
        populationF = PopulationFactory(self.populationSize, individualF)

        #fabrication dune population
        population = populationF.makePopulation()

        #envoie de la population generee
        msg = Message()
        msg.value = [population]
        msg.time = self.timeNext
        self.poke(self.OPorts[0],msg)

    def intTransition(self):
        self.state['sigma'] = INFINITY

    def timeAdvance(self):
        return self.state['sigma']
    
    def __str__(self):
        return "AMPopulationGenLocation"



