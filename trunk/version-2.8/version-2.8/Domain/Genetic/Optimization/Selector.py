from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel
from Domain.Optimization._GAS_ import *

class Selector(SimpleAtomicModel):
    """
    This class ...
    @author: Bastien POGGI
    @organization: University Of Corsica
    @contact: bpoggi@univ-corse.fr
    @since: 2013.05.01
    @version: 1.0
    """

    def __init__(self):
        SimpleAtomicModel.__init__(self)
        self.becomeDesactivate()
        self.mySelector = None

    def extTransition(self):
        self.showScreen("Population evaluated received")
        self.ga = self.readMessage()
        self.mySelector = SelectorHalf(self.ga)
        self.becomeActivate()

    def outputFnc(self):
        self.showScreen("send population selected")
        self.mySelector.select()
        self.showScreen("\n" + str(self.ga))
        self.sendMessage(0,self.ga)

    def intTransition(self):
        self.becomeDesactivate()


    def __str__(self):
        return "Selector"
