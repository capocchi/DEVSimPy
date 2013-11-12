#MODULE AGs
from Domain.Genetic.Lib.Gene import *
from Domain.Genetic.Lib.Individual import IndividualFactory
from Domain.Genetic.Lib.Population import PopulationFactory

#MODULES DEVS
from DomainInterface.DomainBehavior import DomainBehavior
from Domain.Basic.Object import Message

class AMPopulationGenBinary(DomainBehavior):
    """
    This class build a population composed of individual composed themself of Genes type: Binary
    @author: Bastien POGGI
    @organization: University Of Corsica
    @contact: bpoggi@univ-corse.fr
    @since: 2013.01.21
    @version: 1.0
    """
    


    def __init__(self, populationSize=20 ,ADNSize=10, univers="1234567890"):
        """
        @param populationSize:
        @param ADNSize:
        @param univers:
        """
        DomainBehavior.__init__(self)
        
        #ATTRIBUTES
        self.populationSize = populationSize
        self.ADNSize = ADNSize
        self.univers = univers
        
        #INTERNAL STATE
        self.state = {'sigma' : 0}
        
    def outputFnc(self):
        #Createur de caracteres aleatoires
        geneF = GeneCharFactory(self.univers)
        
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
        return "AMPopulationGenBinary"
