Realtime simulation
===================

Realtime simulation is closely linked to normal simulation, with the exception that simulation will not progress as fast as possible. The value returned by the time advance will be interpreted in seconds and the simulator will actually wait (not busy loop) until the requested time has passed. Several realtime backends are supported in PyPDEVS and are mentioned below.

Example model
-------------

The example model will be something else than the *queue* from before, as this isn't really that interesting for realtime simulation. We will instead use the *trafficLight* model. It has a *trafficLight* that is either running autonomous or is in a manual mode. Normally, the traffic light will work autonomously, though it is possible to interrupt the traffic light and switch it to manual mode and back to autonomous again.

This complete model is::

    class TrafficLightMode:
        def __init__(self, current="red"):
            self.set(current)

        def set(self, value="red"):
            self.__colour=value

        def get(self):
            return self.__colour

        def __str__(self):
            return self.get()

    class TrafficLight(AtomicDEVS):
        def __init__(self, name):
            AtomicDEVS.__init__(self, name)
            self.state = TrafficLightMode("red")
            self.INTERRUPT = self.addInPort(name="INTERRUPT")
            self.OBSERVED = self.addOutPort(name="OBSERVED")

        def extTransition(self, inputs):
            input = inputs[self.INTERRUPT][0]
            if input == "toManual":
                if state == "manual":
                    # staying in manual mode
                    return TrafficLightMode("manual")
                if state in ("red", "green", "yellow"):
                    return TrafficLightMode("manual")

            elif input == "toAutonomous":
                if state == "manual":
                    return TrafficLightMode("red")

            raise DEVSException("Unkown input in TrafficLight")

        def intTransition(self):
            state = self.state.get()
            if state == "red":
                return TrafficLightMode("green")
            elif state == "green":
                return TrafficLightMode("yellow")
            elif state == "yellow":
                return TrafficLightMode("red")
            else:
                raise DEVSException("Unkown state in TrafficLight")

        def outputFnc(self):
            state = self.state.get()
            if state == "red":
                return {self.OBSERVED: ["grey"]}
            elif state == "green":
                return {self.OBSERVED: ["yellow"]}
            elif state == "yellow":
                return {self.OBSERVED: ["grey"]}
            else:
                raise DEVSException("Unknown state in TrafficLight")

        def timeAdvance(self):
            if state == "red":
                return 60
            elif state == "green":
                return 50
            elif state == "yellow":
                return 10
            elif state == "manual":
                return INFINITY
            else:
                raise DEVSException("Unknown state in TrafficLight")

With our model being set up, we could run it as-fast-as-possible by starting it like::

    model = TrafficLight("trafficLight")
    sim = Simulator(model)
    sim.simulate()

To make it run in real time, we only need to do some minor changes. First, we need to define on which port we want to put some external input. We can choose a way to address this port, but lets assume that we choose the same name as the name of the port. This gives us::

    refs = {"INTERRUPT": model.INTERRUPT}

Now we only need to pass this mapping to the simulator, together with the choice for realtime simulation. This is done as follows::

    refs = {"INTERRUPT": model.INTERRUPT}
    sim.setRealTime(True)
    sim.setRealTimePorts(refs)

That is all extra configuration that is required for real time simulation. 

As soon as the *simulate()* method is called, the simulation will be started as usual, though now several additional options are enabled. Specifically, the user now has an input prompt to input external data. This input should be of the form *portname data*.

In our example, the model will respond to both *toManual* and *toAutonomous* and we chose *INTERRUPT* in our mapping. So our model will react on the input *INTERRUPT toManual*. To exit realtime simulation, it is best to simply inject 'empty' input. Malformed input will cause an exception and simulation will be halted.

.. note:: All input that is injected will be passed to the model as a *string*. If the model is thus supposed to process integers, a string to integer processing step should happen in the model itself.

Input files
-----------

PyPDEVS also supports the use of input files together with input provided at run time. The input file will be parsed at startup and should be of the form *time port value*, with time being the simulation time at which this input should be injected. Again, this input will always be interpreted as a string. If a syntax error is detected while reading through this file, the error will immediately be shown.

.. note:: The file input closely resembles the usual prompt, though it is not possible to define a termination at a certain time by simply stating the time at the end. For this, you should use the termination time as provided by the standard interface.

An example input file for our example could be::

    10 INTERRUPT toManual
    20 INTERRUPT toAutonomous
    30 INTERRUPT toManual

Backends
--------

Several backends are provided for the realtime simulation. The default backend is the best for most people who just want to simulate in realtime. Other options are for when PyPDEVS is coupled to e.g. a Tk user interface or something with a game loop system.

The following backends are currently supported:

* Python threads: the default, provides simple threading and doesn't require any other programs. Activated with *setRealTimePlatformThreads()*.
* Tk threads: uses Tk for all of its waiting and delays (using the Tk event list). Activated with *setRealTimePlatformTk()*.
* Game loop: requires an external program to call the simulator after a certain delay. Activated with *setRealTimePlatformGameLoop(fps)*.

The game loop mechanism requires some additional explanation:
This mechanism will not block the main thread and if the main thread stops, so will the simulation. The caller has 2 methods to communicate with the threading system after the call to *simulate()*. These methods are:

* *realtime_finished()*: Checks whether or not the simulation is finished.
* *realtime_loop_call()*: Continue to the next simulation step. This advances the internal time according to the value provided in the initialisation.

The game loop mechanism is thus closely linked to the invoker. The calls to the *realtime_loop_call()* function and the initializer are the only concept of time that this mechanism uses. Note that setting the fps to low will decrease the granularity of all actions, as actions are executed during the method invocation.
