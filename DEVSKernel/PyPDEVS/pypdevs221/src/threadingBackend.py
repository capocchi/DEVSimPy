class ThreadingBackend(object):
    """
    Wrapper around the actual threading backend. It will also handle interrupts and the passing of them to the calling thread.
    """
    def __init__(self, subsystem, args):
        """
        Constructor.

        :param subsystem: string specifying the subsystem to use: python, tkinter or loop
        :param args: all additional arguments that should be passed to the subsystem's constructor (must be a list)
        """
        self.interruptedValue = None
        if subsystem == "python":
            from .threadingPython import ThreadingPython
            self.subsystem = ThreadingPython(*args)
        elif subsystem == "tkinter":
            from .threadingTkInter import ThreadingTkInter
            self.subsystem = ThreadingTkInter(*args)
        elif subsystem == "loop":
            from .threadingGameLoop import ThreadingGameLoop
            self.subsystem = ThreadingGameLoop(*args)
        else:
            raise Exception("Realtime subsystem not found: " + str(subsystem))

    def wait(self, time):
        """
        Wait for the specified time using the specified subsystem; interrupts are possible to stop sooner.

        :param time: time to wait in seconds, a float is possible
        :returns: None if the wait was not interrupted; the value passed in the interrupt if the wait was interrupted.
        """
        if time <= 0:
            #### We are running late, so try to catch up. Don't offer the possibility for interrupts to happen and directly return
            # If this situation happens frequently, we might have a problem
            return None
        self.subsystem.wait(time)
        value = self.interruptedValue
        self.interruptedValue = None
        return value

    def interrupt(self, value):
        """
        Interrupt a running wait call.

        :param value: the value that interrupts
        """
        self.interruptedValue = value
        self.subsystem.interrupt()

    def step(self):
        """
        Perform a single step in the simulation.

        .. warning:: Only to be used with the Game Loop subsystem!
        """
        ## Only for looping backend!
        self.subsystem.step()
