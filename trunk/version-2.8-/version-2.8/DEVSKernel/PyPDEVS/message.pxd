cdef class Message:
    cdef public tuple timestamp
    cdef public unsigned short int messagetype
    cdef public dict content

cdef class NetworkMessage(Message):
    cdef public bint antimessage
    cdef public long uuid
    cdef public bint color
    cdef public object destination

    cpdef NetworkMessage copy(self)
