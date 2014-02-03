"""
Relocator for user-provided relocation directives
"""

class MyRelocator(object):
    """
    Main class
    """
    def __init__(self):
        """
        Initialize the relocator
        """
        pass

    def setController(self, controller):
        """
        Sets the controller
        """
        pass

    def getRelocations(self, GVT, activities, horizon):
        """
        Fetch the relocations that are pending for the current GVT

        :param GVT: current GVT
        :param activities: the activities being passed on the GVT ring
        :returns: dictionary containing all relocations
        """
        # Perform a relocation, for example move the model with ID 1 to node 2, and the model with ID 3 to node 0
        # Remaps are allowed to happen to the current location, as they will simply be discarded by the actual relocator
        relocate = {1: 2, 3: 0}
        return relocate

    def lastStateOnly(self):
        """
        Should the sum of all activities within this horizon be used, or simply the activity from the last state?
        This has no effect on performance, but defines which activities the relocator can read.

        Use 'last state only' if you require an abstracted view of the activities at a single timestep (equal to the GVT).
        Use 'all states' if you require all information to be merged, such as in activity tracking.
        """
        # "all states"
        return False
