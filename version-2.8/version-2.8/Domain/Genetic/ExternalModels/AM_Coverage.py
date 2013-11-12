from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from Domain.Genetic.Lib.libDeployment import CoverageCalculator
from Domain.Genetic.Lib.libDeployment import CoverageVizualisation
import csv


class AM_Coverage(SimpleAtomicModel):

#--------------------Initialisation-------------------
    def __init__(self, listSubAreas=[[ (0,0) , (0,100) , (100,100) , (100,0)]],listeSubAreasAttenuations=[1.00], mode="LOG"):
        
        SimpleAtomicModel.__init__(self)
        self.listSubAreas = listSubAreas
        self.listeSubAreasAttenuations = listeSubAreasAttenuations
        self.mode = mode
        
        self.GENERATOR_UTILISE = "LOCATION"
        
        self.becomeDesactivate()
 
#--------------------Fonction entree------------------
    def extTransition(self):
        self.listStrategies = self.readMessage() 
        self.becomeActivate()
        
#--------------------Fonction sortie------------------
    def outputFnc(self):

        #Adaptation sans model traduction precedent
        if self.GENERATOR_UTILISE == "LOCATION":
            conversion = []
            for indiv in self.listStrategies.individuals:
                i = indiv.ADN
                i = map(lambda x: (x.lat, x.lon, 10), i)
                conversion.append(i)
            self.listStrategies = conversion
        #------------------------------------------
        
        listFitness = []
        for strategie in self.listStrategies:
            c = CoverageCalculator(self.listSubAreas, self.listeSubAreasAttenuations, strategie)
            listFitness.append(c.coverateRate)
        
        CoverageVizualisation(c)
            
        self.showScreen(max(listFitness))
        
        self.sendMessage(0,listFitness)

#--------------------Fonction interne------------------
    def intTransition(self):
        self.becomeDesactivate()

#--------------------Fonction ToString------------
    def __str__(self):
        return "AM_Coverage"
        
        
