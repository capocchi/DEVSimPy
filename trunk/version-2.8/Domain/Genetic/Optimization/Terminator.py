from Domain.Genetic.Lib.SimpleAtomicModel import SimpleAtomicModel

class Terminator(SimpleAtomicModel):
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


    def extTransition(self):
        pass
        

    def outputFnc(self):
        pass


    def intTransition(self):
        pass


    def __str__(self):
        return "Terminator"
