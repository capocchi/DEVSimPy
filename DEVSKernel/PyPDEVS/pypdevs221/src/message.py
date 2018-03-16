"""
Network messages used in the distributed simulation
"""

class NetworkMessage(object):
    """
    Network messages used in the distributed simulation, simply a data class.
    """
    def __init__(self, timestamp, content, uuid, color, destination):
        """
        Constructor

        :param timestamp: timestamp of the message
        :param content: content of the message
        :param uuid: UUID of the message
        :param color: color of the message for Mattern's algorithm
        :param destination: the model_id of the destination model
        """
        self.timestamp = timestamp
        self.content = content
        self.uuid = uuid
        self.color = color
        self.destination = destination

    def __str__(self):
        """
        String representation of the message
        """
        return "NetworkMessage:\n\t%s\n\t%s\n\t%s\n\t%s\n\t%s" % (self.timestamp, self.content, self.uuid, self.color, self.destination)

    def __lt__(self, other):
        """
        Comparison of different NetworkMessages, necessary for Python3
        """
        return self.timestamp < other.timestamp
