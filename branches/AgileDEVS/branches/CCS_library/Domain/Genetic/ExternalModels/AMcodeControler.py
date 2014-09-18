from DomainInterface.DomainBehavior import DomainBehavior
from Domain.Basic.Object import Message

class AMcodeControler(DomainBehavior):


    def __init__(self,nameEval="CODE CONTROLER", code="1234567890"):
        DomainBehavior.__init__(self)       
        self.Evalname = nameEval
        self.code = code
        
        self.state = {'sigma':INFINITY }
        self.evaluationList = []

#--------------------Fonction entree------------------
    def extTransition(self):
        print self.Evalname," : RECEPTION"
        msg = self.peek(self.IPorts[0])
        self.population = msg.value[0]
        for individual in self.population.individuals:
            self.evaluationList.append(self.simulate(individual))
        print self.Evalname," : EVALUATION TERMINEE"
        self.state['sigma'] = 0
        
 #--------------------Fonction sortie------------------       
    def outputFnc(self):
        print self.Evalname," : ENVOI RESULTATS EVALUATION"
        msg = Message()
        print self.evaluationList
        msg.value = [self.evaluationList]
        msg.time = self.timeNext
        self.poke(self.OPorts[0],msg)

#--------------------Fonction interne------------------
    def intTransition(self):
        self.state['sigma'] = INFINITY
        self.evaluationList = []

#--------------------Fonction TA------------------
    def timeAdvance(self):
        return self.state['sigma']

#--------------------Fonction ToString------------
    def __str__(self):
        return "AMcodeControler"

    def simulate(self, individual):
        eval = 0
        #Verification de la longueur de la chaine
        if len(individual.ADN) == len(self.code):
            #print "ADN et code de meme longueur---------"
            for i in range(len(self.code)):
                if str(individual.ADN[i]) == str(self.code[i]):
                    #print "egal"
                    eval += 1
                #else:
                #    print "different"

        else:
            print "Taille du code genetique different du code"
            #print "Taille invidu", len(self.code)
            #print "Taille code", len(individual.ADN)
        return eval
        
