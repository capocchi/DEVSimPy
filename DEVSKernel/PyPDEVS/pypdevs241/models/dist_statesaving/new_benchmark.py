# New benchmark that only compares different methods in function of the state complexity
# This benchmark works out of the context of a real simulation!

# Complexity is defined as the number of attributes
from copy import deepcopy
import pickle as pickle
import time
import random

class AttributesState(object):
    def __init__(self, complexity):
        self.complexity = complexity
        for f in range(complexity):
            setattr(self, str(f), None)

    def set_initial(self):
        for f in range(complexity):
            setattr(self, str(f), random.random())

    def copy(self):
        a = AttributesState(self.complexity)
        for f in range(self.complexity):
            setattr(a, str(f), getattr(self, str(f)))
        return a

class SizeState(object):
    def __init__(self, complexity):
        self.values = [None] * complexity
        self.complexity = complexity

    def set_initial(self):
        self.values = [random.random() for _ in range(complexity)]

    def copy(self):
        a = SizeState(self.complexity)
        a.values = list(self.values)
        return a

def benchmark(s, f, out):
    samples = 1000
    for c in range(0, 300, 5):
        if s == "AttributesState":
            state = AttributesState(c)
        elif s == "SizeState":
            state = SizeState(c)
        start = time.time()
        for _ in range(samples):
            f(state)
        t = (time.time() - start) / samples * 1000
        print(("%i %f" % (c, t)))
        out.write("%i %f\n" % (c, t))

for s in ["AttributesState", "SizeState"]:
    for f in [("deepcopy", lambda i: deepcopy(i)), ("pickle", lambda i: pickle.loads(pickle.dumps(i))), ("custom", lambda i: i.copy())]:
        print(("%s -- %s" % (s, f[0])))
        out = open("%s_%s" % (s, f[0]), 'w')
        benchmark(s, f[1], out)
        out.close()
