from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
import sys


class AM_Glycemia(SimpleAtomicModel):

#--------------------Initialisation-------------------
    def __init__(self):
        SimpleAtomicModel.__init__(self)        
        #BSN (body sensor network values)
        self.normal_glycemic_level = [0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 1.0, 1.5, 1.42, 1.32, 1.25, 1.75, 
        2.25, 2.17, 2.09, 2.0, 1.92, 1.84, 1.75, 2.05, 2.375, 2.6875, 3.0, 2.92, 2.84]
        #DRUG caracteristics
        self.drugEffectPerMg = 0.10
        self.drugTimeLife = 5
        self.effects = []
        self.becomeActivate()
        
 
    def extTransition(self):  
        print "ENTRE"
        taking_drug = self.readMessage()
        print "\nInjection de %s mg"%taking_drug
        self.updateEffects(float(taking_drug))
        self.test = 1   
        self.state = {'sigma' : 0}

    def outputFnc(self):
        print "SORTIE self.test"
        #Valeur avec traitement
        if self.effects != []:
            valeur_avec_traitement = self.normal_glycemic_level[0] + self.effects[0]
            del self.effects[0]
        else:
            valeur_avec_traitement = self.normal_glycemic_level[0]
        
        
        self.sendMessage(0,self.normal_glycemic_level[0])
        self.sendMessage(1,valeur_avec_traitement)
        self.sendMessage(2,0.75)
        

        del self.normal_glycemic_level[0]


    def intTransition(self):
        self.state = {'sigma' : 1}


    def __str__(self):
        return "AM_Glycemia"
        
        
    def updateEffects(self,taking_drug):
        new_effects = [(self.drugEffectPerMg * -taking_drug) for i in range(self.drugTimeLife)]
        print "Nouveaux effets",new_effects
        print "Anciens effets", self.effects
        if self.effects == []: 
                self.effects = new_effects
        else:
            for i,val in enumerate(new_effects):
                if i < len(self.effects):
                    new_effects[i] += self.effects[i]        
            self.effects = new_effects
        print self.effects
                
        
