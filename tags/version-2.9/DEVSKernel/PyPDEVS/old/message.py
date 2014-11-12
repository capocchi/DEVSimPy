# Message types:
# 0 --> init message
# 1 --> perform transition function
# 2 --> collect output
# 3 --> receive external input

#cython cdef class Message:
class Message(object): #cython-remove
    def __init__(self, timestamp, messagetype, content = {}):
        self.timestamp = timestamp
        self.messagetype = messagetype
        self.content = content

    def __reduce__(self):
        return (genMessage, (self.timestamp, self.messagetype, self.content))

    def __str__(self):
        return "Message:\n\t%s\n\t%s\n\t%s" % (self.timestamp, self.messagetype, str(self.content))

#cython cdef class NetworkMessage(Message):
class NetworkMessage(Message): #cython-remove
    def __init__(self, message, antimessage, uuid, color, destination=None):
        Message.__init__(self, message.timestamp, message.messagetype, message.content)
        self.antimessage = antimessage
        self.uuid = uuid
        self.color = color
        self.destination = destination

    def __reduce__(self):
        # No need to think about content (which could contain a Port object), since this will already be remapped
        return (genNetworkMessage, (self.timestamp, self.messagetype, self.content, self.antimessage, self.uuid, self.color, self.destination))

    def __str__(self):
        return "NetworkMessage:\n\t%s\n\t%s\n\t%s\n\t%s\n\t%s\n\t%s" % (self.timestamp, self.content, self.antimessage, self.uuid, self.color, self.destination)

    #cython cpdef NetworkMessage copy(self):
    def copy(self): #cython-remove
        return NetworkMessage(Message(self.timestamp, self.messagetype, self.content), self.antimessage, self.uuid, self.color, self.destination)

def genMessage(timestamp, messagetype, content):
    return Message(timestamp, messagetype, content)

def genNetworkMessage(timestamp, messagetype, content, antimsg, uuid, color, destination):
    return NetworkMessage(Message(timestamp, messagetype, content), antimsg, uuid, color, destination)
