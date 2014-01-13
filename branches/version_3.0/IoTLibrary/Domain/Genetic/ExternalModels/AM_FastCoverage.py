from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from Domain.Genetic.Lib.libDeployment import FastCoverageCalculator
import csv


class AM_FastCoverage(SimpleAtomicModel):

#--------------------Initialisation-------------------
    def __init__(self, listSubAreas=[[ (0,0) , (20,0) , (25,45) , (50,100), (0,100) ],[ (20,0), (25,45), (50,100), (90,100), (65,40), (80,0)],[ (80,0), (100,0), (100,100), (90,100), (65,40), (80,0)]],listeSubAreasAttenuations=[0.80,0.20,0.01],mode='LOG'):
        
        SimpleAtomicModel.__init__(self)
        self.listSubAreas = listSubAreas
        self.listeSubAreasAttenuations = listeSubAreasAttenuations
        self.historicBest = []
        self.historicWorst = []
        
        self.mode=mode
        
        self.logs = csv.writer(open('evalutor.csv','wb'),delimiter=":")
        
        self.GENERATOR_UTILISE = "LOCATION"
        
        self.becomeDesactivate()
        
#--------------------Fonction entree------------------
    def extTransition(self):
        self.listStrategies = self.readMessage() 

        #Adaptation sans model traduction precedent
        if self.GENERATOR_UTILISE == "LOCATION":
            conversion = []
            for indiv in self.listStrategies.individuals:
                i = indiv.ADN
                i = map(lambda x: (x.lat, x.lon, 10), i)
                conversion.append(i)
            self.listStrategies = conversion
        #------------------------------------------
        self.becomeActivate()
        
#--------------------Fonction sortie------------------
    def outputFnc(self): 
        listFitness = []
        listRepartition = []
        
        for strategie in self.listStrategies:
            c = FastCoverageCalculator(self.listSubAreas, self.listeSubAreasAttenuations, strategie)
            listFitness.append(c.coverateRate)
            listRepartition.append(c.repartition)
            
        
        bestFitness = max(listFitness)        
        worstFitness = min(listFitness)
        self.historicBest.append(bestFitness)
        self.historicWorst.append(worstFitness)
        
        best = self.listStrategies[listFitness.index(bestFitness)]
        worst = self.listStrategies[listFitness.index(worstFitness)]
        
        bestRepartition =  listRepartition[listFitness.index(bestFitness)]
        self.showScreen(bestFitness)

        self.logs.writerow([bestFitness, worstFitness, str(best), str(worst),bestRepartition])
        
        self.sendMessage(0,listFitness)
        
        self.sendMessage(1, map(lambda x: x[0],listRepartition))
        self.sendMessage(2, map(lambda x: x[1],listRepartition))
        self.sendMessage(3, map(lambda x: x[2],listRepartition))    

#--------------------Fonction interne------------------
    def intTransition(self):
        self.becomeDesactivate()

#--------------------Fonction ToString------------
    def __str__(self):
        return "AM_FastCoverage"
        
        
