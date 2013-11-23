from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel

class AM_Controler(SimpleAtomicModel):
#--------------------Initialisation-------------------
    def __init__(self, numberGenerationCheck=200, expectedVariationRate=10):
        
        SimpleAtomicModel.__init__(self)
        self.becomeDesactivate()
        
        self.numberIterations = 0


    def extTransition(self):
        self.population = self.readMessage()
        self.check()
    

    def outputFnc(self):
        #Order management
        for order in self.ordersToSend:
            self.sendMessage(order.numOutputPort, order.order)        

    def intTransition(self):
        self.becomeDesactivate()
        self.numberIterations += 1
        self.previousBestFitness = self.getBest()


    def __str__(self):
        return "PyramidalSatisfaction"
        
    def check(self):
        if self.numberIterations % numberGenerationCheck and self.realVariationRate < expectedVariationRate:
            self.updateConfiguration()
            
    def updateConfiguration(self):
        #Mutation Variation

        #Reproduction Variation

        #Population Variation

        #Evaluation Variation
        pass
        
    def getBest(self):
        pass
    
class AM_Controler_Message:
    
    ORDERS = ["UPDATE_GENERATOR",
            "UPDATE_EVALUATOR",
            "UPDATE_SELECTOR",
            "UPDATE_MUTATOR"]
    
    def __init__(self, order, numOutputPort):
        self.order = order
        self.numOutputPort = numOutputPort