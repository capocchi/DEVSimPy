import threading
import queue

from . import RTthreads

class PythonThreads:
 def __init__(self):
    self.eventSignal  = threading.Event() # for signalling presence of event
                                  # eventSender -> eventReceiver
    self.interruptedByEvent = False
    self.interruptedLock = threading.Lock() # to protect interruptedByEvent
    self.globalLock = threading.Lock()
    self.running = []
    self.cancelables = []

 def start(self, function):
    self.thread = threading.Thread(target=function)
    self.thread.daemon = True
    self.thread.start()

 def scheduleAfter(self, time, function, args):
    thrd = threading.Thread(target=self.wait, args=[time, function, args])
    thrd.daemon = True
    thrd.start()

 def wait(self, time, function, args = None):
    time = float(time)
    evt = threading.Event()
    self.running.append(evt)
    if args == None:
        # internal event
        # CANCELABLE
        self.cancelables.append(evt)
        args = []
    if(evt.wait(time)):
        # We did not time out, but were interrupted :(
        return
    else:
        # OK, our time has passed, so ready to execute
        # First invalidate all other events (that are possible to invalidate)
        for i in self.cancelables:
            i.set()
        #self.cancelables = []
        function(*args)

 def end(self):
        self.thread.join(2**31)

 def stop(self):
        # Nothing we can do
        pass

class TkinterThreads:
        interruptedByEvent = False
        interruptedLock = threading.Lock() # to protect interruptedByEvent
        mainFunction = None
        runningIDs = []
        toRun = queue.Queue()
        tk = None

        def start(self, function):
            self.thread = threading.Thread(target=function)
            self.thread.daemon = True
            self.thread.start()

        def runfnc(self, function, *args):
            for i in TkinterThreads.runningIDs:
                TkinterThreads.tk.after_cancel(i)
            function(*args)

        def scheduleAfter(self, time, function, args):
            if args == None:
                args = [function]
            else:
                arg = [function]
                arg.extend(args)
                args = arg
            TkinterThreads.toRun.put((int(1000*float(time)), self.runfnc, args))

        def end(self):
                pass

        def stop(self):
                TkinterThreads.runningIDs = []

        @staticmethod
        def performActions():
                try:
                    time, function, args = TkinterThreads.toRun.get_nowait()
                    evt = TkinterThreads.tk.after(time, function, *args)
                    if len(args) == 1:
                        TkinterThreads.runningIDs.append(evt)
                    elif len(args) == 2 and args[1] == "":
                        TkinterThreads.tk.quit()
                except queue.Empty:
                    pass
                TkinterThreads.tk.after(10, TkinterThreads.performActions)

class EventThread:
        listLock = threading.Lock()
        eventBuffer = ""
        bufferLock = threading.Lock()
        threadList = []

        # Will get overwritten at startup of main
        core = None

        def __init__(self, subsystem = None):
                self.subsystem = subsystem

        def wait(self, time, function, cancelable=True):
                self.subsystem.wait(time, function, cancelable)

        def end(self):
                self.subsystem.end()

        def start(self, function):
                self.subsystem.start(function)

        def stop(self):
                self.subsystem.stop()

        def scheduleAfter(self, time, function, inp = None):
            self.subsystem.scheduleAfter(time, function, inp)
