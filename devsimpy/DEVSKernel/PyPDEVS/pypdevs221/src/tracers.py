import importlib
 
class Tracers(object):
    """
    Interface for all tracers
    """
    def __init__(self):
        """
        Constructor
        """
        self.tracers = []
        self.tracers_init = []
        self.uid = 0

    def registerTracer(self, tracer, server, recover):
        """
        Register a tracer, so that it will also receive all transitions.

        :param tracer: tuple of the form (file, classname, [args])
        :param controller: is this code ran at the controller?
        TODO
        """
        ###Py 3.0
        tv = importlib.import_module("DEVSKernel.PyPDEVS.pypdevs221.src.%s"%tracer[0])
    
        self.tracers.append(eval("tv.%s(%i, server, *%s)" % (tracer[1], self.uid, tracer[2])))
        self.tracers_init.append(tracer)
        self.uid += 1
        self.tracers[-1].startTracer(recover)

    def hasTracers(self):
        """
        Checks whether or not there are any registered tracers

        :returns: bool
        """
        return len(self.tracers) > 0

    def getByID(self, uid):
        """
        Gets a tracer by its UID

        :param uid: the UID of the tracer to return
        :returns: tracer
        """
        return self.tracers[uid]

    def stopTracers(self):
        """
        Stop all registered tracers
        """
        for tracer in self.tracers:
            tracer.stopTracer()

    def tracesUser(self, time, aDEVS, variable, value):
        """
        TODO
        """
        for tracer in self.tracers:
            try:
                tracer.traceUser(time, aDEVS, variable, value)
            except AttributeError:
                # Some tracers choose to ignore this event
                pass

    def tracesInit(self, aDEVS):
        """
        Perform all tracing actions for an initialisation
        
        :param aDEVS: the model that was initialised
        """
        for tracer in self.tracers:
            tracer.traceInit(aDEVS)

    def tracesInternal(self, aDEVS):
        """
        Perform all tracing actions for an internal transition
        
        :param aDEVS: the model that transitioned
        """
        for tracer in self.tracers:
            tracer.traceInternal(aDEVS)

    def tracesExternal(self, aDEVS):
        """
        Perform all tracing actions for an external transition
        
        :param aDEVS: the model that transitioned
        """
        for tracer in self.tracers:
            tracer.traceExternal(aDEVS)

    def tracesConfluent(self, aDEVS):
        """
        Perform all tracing actions for a confluent transition
        
        :param aDEVS: the model that transitioned
        """
        for tracer in self.tracers:
            tracer.traceConfluent(aDEVS)
