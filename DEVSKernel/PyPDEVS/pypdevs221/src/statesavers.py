"""
Different methods to save the state, this allows for more modularity than just having a big switch statement in the main code.
Note that these classes are not subclasses of a more generic class, as this allows these classes to save data in a completely
different manner from each other. Furthermore, it avoids (slow) inheritance.
"""
from copy import deepcopy, copy
try:
    import pickle as pickle
except ImportError:
    import pickle
import marshal

class DeepCopyState(object):
    """
    Class to save the state using the Python 'deepcopy' library
    """
    def __init__(self, timeLast, timeNext, state, activity, myInput, elapsed):
        """
        Constructor

        :param timeLast: timeLast to save
        :param timeNext: timeNext to save
        :param state: state to save
        :param activity: the activity of the computation
        :param myInput: the state input to save for memorisation
        :param elapsed: the time elapsed
        """
        self.timeLast = timeLast
        self.timeNext = timeNext
        self.activity = activity
        self.state = deepcopy(state)
        self.myInput = myInput
        self.elapsed = elapsed

    def loadState(self):
        """
        Load the state from the class, this will make a copy

        :returns: state - copy of the state that was saved
        """
        return deepcopy(self.state)

class CopyState(object):
    """
    Class to save the state using the Python 'copy' library
    """
    def __init__(self, timeLast, timeNext, state, activity, myInput, elapsed):
        """
        Constructor

        :param timeLast: timeLast to save
        :param timeNext: timeNext to save
        :param state: state to save
        :param activity: the activity of the computation
        :param myInput: the state input to save for memorisation
        :param elapsed: the time elapsed
        """
        self.timeLast = timeLast
        self.timeNext = timeNext
        self.activity = activity
        self.state = copy(state)
        self.myInput = myInput
        self.elapsed = elapsed

    def loadState(self):
        """
        Load the state from the class, this will make a copy

        :returns: state - copy of the state that was saved
        """
        return copy(self.state)

class AssignState(object):
    """
    Class to save the state using a simple assignment, is unsafe for most situations...
    """
    def __init__(self, timeLast, timeNext, state, activity, myInput, elapsed):
        """
        Constructor

        :param timeLast: timeLast to save
        :param timeNext: timeNext to save
        :param state: state to save
        :param activity: the activity of the computation
        :param myInput: the state input to save for memorisation
        :param elapsed: the time elapsed
        """
        self.timeLast = timeLast
        self.timeNext = timeNext
        self.activity = activity
        self.state = state
        self.myInput = myInput
        self.elapsed = elapsed

    def loadState(self):
        """
        Load the state from the class, this will make a copy

        :returns: state - copy of the state that was saved
        """
        return self.state

class PickleZeroState(object):
    """
    Class to save the state using the Python 'pickle' library, with the option to use the pickling protocol 0.
    """
    def __init__(self, timeLast, timeNext, state, activity, myInput, elapsed):
        """
        Constructor

        :param timeLast: timeLast to save
        :param timeNext: timeNext to save
        :param state: state to save
        :param activity: the activity of the computation
        :param myInput: the state input to save for memorisation
        :param elapsed: the time elapsed
        """
        self.timeLast = timeLast
        self.timeNext = timeNext
        self.activity = activity
        self.state = pickle.dumps(state, 0)
        self.myInput = myInput
        self.elapsed = elapsed

    def loadState(self):
        """
        Load the state from the class, this will make a copy

        :returns: state - copy of the state that was saved
        """
        return pickle.loads(self.state)

class PickleHighestState(object):
    """
    Class to save the state using the Python 'pickle' library, with the option to use the highest available pickling protocol.
    """
    def __init__(self, timeLast, timeNext, state, activity, myInput, elapsed):
        """
        Constructor

        :param timeLast: timeLast to save
        :param timeNext: timeNext to save
        :param state: state to save
        :param activity: the activity of the computation
        :param myInput: the state input to save for memorisation
        :param elapsed: the time elapsed
        """
        self.timeLast = timeLast
        self.timeNext = timeNext
        self.activity = activity
        self.state = pickle.dumps(state, pickle.HIGHEST_PROTOCOL)
        self.myInput = myInput
        self.elapsed = elapsed

    def loadState(self):
        """
        Load the state from the class, this will make a copy

        :returns: state - copy of the state that was saved
        """
        return pickle.loads(self.state)

class CustomState(object):
    """
    Class to save the state using a manually defined copy() function of the state. If no such method is provided, an error is raised.
    """
    def __init__(self, timeLast, timeNext, state, activity, myInput, elapsed):
        """
        Constructor

        :param timeLast: timeLast to save
        :param timeNext: timeNext to save
        :param state: state to save
        :param activity: the activity of the computation
        :param myInput: the state input to save for memorisation
        :param elapsed: the time elapsed
        """
        self.timeLast = timeLast
        self.timeNext = timeNext
        self.activity = activity
        self.state = state.copy()
        self.myInput = myInput
        self.elapsed = elapsed

    def loadState(self):
        """
        Load the state from the class, this will make a copy

        :returns: state - copy of the state that was saved
        """
        return self.state.copy()

class MarshalState(object):
    """
    Class to save the state using the Python 'marshal' library.
    """
    def __init__(self, timeLast, timeNext, state, activity, myInput, elapsed):
        """
        Constructor

        :param timeLast: timeLast to save
        :param timeNext: timeNext to save
        :param state: state to save
        :param activity: the activity of the computation
        :param myInput: the state input to save for memorisation
        :param elapsed: the time elapsed
        """
        self.timeLast = timeLast
        self.timeNext = timeNext
        self.activity = activity
        self.state = marshal.dumps(state)
        self.myInput = myInput
        self.elapsed = elapsed

    def loadState(self):
        """
        Load the state from the class, this will make a copy

        :returns: state - copy of the state that was saved
        """
        return marshal.loads(self.state)
