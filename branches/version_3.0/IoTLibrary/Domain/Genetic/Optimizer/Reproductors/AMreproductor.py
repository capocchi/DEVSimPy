#MODULES DEVS
from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from Domain.Genetic.Lib.CrossOver import CrossOverHalfAndHalf
from Domain.Genetic.Lib.CrossOver import CrossOverOneOfTwo

class AMreproductor(SimpleAtomicModel):

#-----------------------------------------------------

    def __init__(self,mode="LOG"):
        SimpleAtomicModel.__init__(self)
        self.mode = mode
        self.becomeDesactivate()

#-----------------------------------------------------

    def extTransition(self):
        self.showScreen("RECEPTION DUNE POPULATION")
        self.population = self.readMessage()
        self.makeReproductionProcess()
        self.becomeActivate()

#-----------------------------------------------------

    def outputFnc(self):
        self.showScreen("ENVOIS DE LA NOUVELLE POPULATION")
        self.sendMessage(0,self.population)

#-----------------------------------------------------

    def intTransition(self):
        self.becomeDesactivate()

#-----------------------------------------------------

    def __str__(self):
        return "AMreproductor"

#-----------------------------------------------------

#GESTION DE LA FUSION

    def makeReproductionProcess(self):
        #SELECTION DES REPRODUCTEURS
        reproductors = filter(lambda individual: individual.reproductor, self.population.individuals) #LIST DES MEILLEURS INDIVIDUS
        reproductors.reverse()
        self.showScreen("LE NOMBRE DE REPRODUCTEUR EST" + str(len(reproductors)))
        
        children = self.makeChildren(reproductors)
        self.showScreen(str(len(children))+ "NOUVEAUX INDIVIDUS ONT ETE CREES")

        self.population.integrateChildren(children)
        self.showScreen(str(len(children)) + "ANCIENS INDIVIDUS ONT ETE REMPLASSES")


    def makeChildren(self, parents):
        children = []
        for i in range(0, len(parents)-1, 2):
            
#            print "creation de lenfant de", i, "et ", i+1
            crossOver = CrossOverHalfAndHalf(parents[i], parents[i+1]) #ENFANT PERE ET MERE
            children.append(crossOver.createChild())
            
#             print "------"
#             print "PARENT A", parents[i].ADN
#             print "PARENT B",parents[i+1].ADN
#             print "ENFANT C",children[0].ADN
#             print "------"
            
#            print "creation de lenfant de", i+1, "et ", i
            crossOver = CrossOverHalfAndHalf(parents[i+1], parents[i]) # ENFANT MERE ET PERE
            children.append(crossOver.createChild())
            
            
        return children #LISTE DES ENFANTS CRES




