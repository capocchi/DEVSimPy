from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from Domain.Optimization._GAS_ import *

class Evaluator(SimpleAtomicModel):
    """
    This class ...
    @author: Bastien POGGI
    @organization: University Of Corsica
    @contact: bpoggi@univ-corse.fr
    @since: 2013.05.01
    @version: 1.0
    """

    def __init__(self, weights=[0.80,0.20]):
        SimpleAtomicModel.__init__(self)
        self.becomeDesactivate()
        self.myEvaluator = None
        self.weights = weights
        
    def extTransition(self):
        self.showScreen("Receive population generated")
        self.ga = self.readMessage()
        self.myEvaluator = EvaluatorDEVS(self.ga, self.weights)
        
        
        self.becomeActivate()


        

    def outputFnc(self):
        self.myEvaluator.evaluate()
        self.showScreen("\n" + str(self.ga))
        self.sendMessage(0,self.ga)


    def intTransition(self):
        self.becomeDesactivate()


    def __str__(self):
        return "Evaluator"
