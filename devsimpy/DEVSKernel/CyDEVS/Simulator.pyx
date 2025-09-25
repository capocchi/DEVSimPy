# cython: language_level=3
from itertools import *
import threading
import array
from .DEVS import CoupledDEVS, AtomicDEVS, INFINITY

cdef class Sender:
    def t_send(self, X, imm, t):
        threads = []
        for m in X:
            thread = ThreadingAtomicSolver(m, (dict(X[m]), imm, t))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.finish()
    def send(self, d, msg):
        if isinstance(d, CoupledDEVS):
            CS = CoupledSolver()
            r = CS.receive(d, msg)
        else:
            AS = AtomicSolver()
            r = AS.receive(d, msg)
        return r

class ThreadingAtomicSolver(threading.Thread):
    def __init__(self, d, msg):
        threading.Thread.__init__(self)
        self.value = {}
        self.alive = False
        self.d = d
        self.msg = msg
    def run(self):
        self.alive = True
        self.receive(self.d, self.msg)
    def receive(self, d, msg):
        self.value = AtomicSolver.receive(d, msg)
    def peek(self):
        return self.value
    def finish(self):
        self.alive = False
        return self.value

class AtomicSolver:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AtomicSolver, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    @staticmethod
    def receive(aDEVS, msg):
        t = msg[2]
        if msg[0] == 1:
            if t != aDEVS.timeNext:
                raise Exception("Bad synchronization...1")
            aDEVS.myOutput = {}
            aDEVS.outputFnc()
            aDEVS.elapsed = t - aDEVS.timeLast
            aDEVS.intTransition()
            aDEVS.timeLast = t
            aDEVS.myTimeAdvance = aDEVS.timeAdvance()
            aDEVS.timeNext = aDEVS.timeLast + aDEVS.myTimeAdvance
            if aDEVS.myTimeAdvance != INFINITY:
                aDEVS.myTimeAdvance += t
            aDEVS.elapsed = 0
            return aDEVS.myOutput
        elif isinstance(msg[0], dict):
            if not(aDEVS.timeLast <= t <= aDEVS.timeNext):
                raise Exception("Bad synchronization...2")
            aDEVS.myInput = msg[0]
            aDEVS.elapsed = t - aDEVS.timeLast
            aDEVS.extTransition()
            aDEVS.timeLast = t
            aDEVS.myTimeAdvance = aDEVS.timeAdvance()
            aDEVS.timeNext = aDEVS.timeLast + aDEVS.myTimeAdvance
            if aDEVS.myTimeAdvance != INFINITY:
                aDEVS.myTimeAdvance += t
            aDEVS.elapsed = 0
        elif msg[0] == 0:
            aDEVS.timeLast = t - aDEVS.elapsed
            aDEVS.myTimeAdvance = aDEVS.timeAdvance()
            aDEVS.timeNext = aDEVS.timeLast + aDEVS.myTimeAdvance
            if aDEVS.myTimeAdvance != INFINITY:
                aDEVS.myTimeAdvance += t
        else:
            raise Exception("Unrecognized message")

class CoupledSolver(Sender):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Sender, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    def threading_send(self, Y, cDEVS, t):
        send = self.send
        cDEVS.timeLast = t
        cDEVS.myTimeAdvance = INFINITY
        cDEVS.myOutput.clear()
        imm = cDEVS.immChildren
        X = {}
        for p in Y:
            a = Y[p]
            for pp in p.outLine:
                b = pp.host
                if b not in X:
                    X[b] = [(pp, a)]
                else:
                    X[b].append((pp, a))
                if b is CoupledDEVS:
                    cDEVS.myOutput[b] = a
        for m in X:
            send(m, (dict(X[m]), imm, t))
    def receive(self, cDEVS, msg):
        t = msg[2]
        send = self.send
        if msg[0] == 1:
            if t != cDEVS.myTimeAdvance:
                raise Exception("Bad synchronization...3")
            try:
                dStar = cDEVS.select(cDEVS.immChildren)
            except IndexError:
                raise IndexError
            self.threading_send(send(dStar, msg), cDEVS, t)
            time_advances = [c.myTimeAdvance for c in cDEVS.componentSet]
            cDEVS.myTimeAdvance = min(time_advances + [cDEVS.myTimeAdvance])
            cDEVS.immChildren = [d for d, ta in zip(cDEVS.componentSet, time_advances) if cDEVS.myTimeAdvance == ta]
            return cDEVS.myOutput
        elif isinstance(msg[0], dict):
            if not(cDEVS.timeLast <= t <= cDEVS.myTimeAdvance):
                raise Exception("Bad synchronization...4")
            cDEVS.myInput = msg[0]
            self.threading_send(cDEVS.myInput, cDEVS, t)
            time_advances = [d.myTimeAdvance for d in cDEVS.componentSet]
            cDEVS.myTimeAdvance = min(time_advances + [cDEVS.myTimeAdvance])
            cDEVS.immChildren = [d for d, ta in zip(cDEVS.componentSet, time_advances) if cDEVS.myTimeAdvance == ta]
        elif msg[0] == 0:
            cDEVS.timeLast = 0
            cDEVS.myTimeAdvance = INFINITY
            for d in cDEVS.componentSet:
                self.send(d, msg)
                cDEVS.myTimeAdvance = min(cDEVS.myTimeAdvance, d.myTimeAdvance)
                cDEVS.timeLast = max(cDEVS.timeLast, d.timeLast)
            cDEVS.immChildren = [d for d in cDEVS.componentSet if cDEVS.myTimeAdvance == d.myTimeAdvance]
        else:
            raise Exception("Unrecognized message")

cdef class Simulator(Sender):
    def __init__(self, model=None):
        self.model = model
        self.__augment(self.model)
    def __augment(self, d=None):
        d.timeLast = d.myTimeAdvance = 0.
        if isinstance(d, CoupledDEVS):
            for subd in d.componentSet:
                self.__augment(subd)