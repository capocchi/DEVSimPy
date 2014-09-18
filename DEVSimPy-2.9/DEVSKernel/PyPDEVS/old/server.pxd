cdef class Server:
    cdef list simstack
    cdef object name
    cdef object daemon
    cdef object threadpool
    cdef object nextLP
    cdef unsigned short size
    cdef object nextLPid
    cdef list locations
