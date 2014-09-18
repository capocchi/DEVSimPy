#MODULE AGs
from Domain.Genetic.Lib.Gene import *
from Domain.Genetic.Lib.Individual import IndividualFactory
from Domain.Genetic.Lib.Population import PopulationFactory

#MODULES DEVS
from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel

class AMPopulationGenBinary(SimpleAtomicModel):
    """
    This class build a population composed of individual composed themself of Genes type: Binary
    @author: Bastien POGGI
    @organization: University Of Corsica
    @contact: bpoggi@univ-corse.fr
    @since: 2013.01.21
    @version: 1.0
    """
    
    def __init__(self, populationSize=3 ,numberGene=50, numberBitsPerGene=14, mode="LOG"):
        """
        @param populationSize:
        @param ADNSize:
        """
        SimpleAtomicModel.__init__(self)
        
        #ATTRIBUTES
        self.populationSize = populationSize
        self.ADNSize = numberGene * numberBitsPerGene
        self.mode = mode
        
        #INTERNAL STATE
        self.becomeActivate()
        
    def outputFnc(self):
        #Createur de caracteres aleatoires
        geneF = GeneBinFactory()
        
        #instansiation de l'individu (une liste de genes possibles)
        individualF = IndividualFactory(self.ADNSize, geneF)
        
        #instansiation de la population (une liste dindividus)
        populationF = PopulationFactory(self.populationSize, individualF)
        
        #fabrication dune population
        population = populationF.makePopulation()
        
        self.sendMessage(0,population)
        self.showScreen("ENVOI DUNE POPULATION ALEATOIRE")

    def intTransition(self):
        self.becomeDesactivate()

    def timeAdvance(self):
        return self.state['sigma']
    
    def __str__(self):
        return "AMPopulationGenBinary"
