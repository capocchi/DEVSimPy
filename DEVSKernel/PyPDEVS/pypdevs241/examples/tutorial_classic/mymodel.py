from pypdevs.DEVS import AtomicDEVS

class MyModel(AtomicDEVS):
    def __init__(self):
        AtomicDEVS.__init__(self, "example")
