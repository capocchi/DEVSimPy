import select
import sys
import threading
import time

class AsynchronousComboGenerator(object):
    """
    The asynchronous combo generator: it generates events from both file input, or from user input, without blocking
    """
    def __init__(self, filename, backend, scale):
        """
        Constructor.

        :param filename: the name of the input file to use for file input. None for no file input.
        :param backend: subsystem to use for threading
        :param scale: realtime scale to use

        .. note:: *filename* parameter should not be a file handle
        """
        self.filename = filename
        self.backend = backend
        # Start the generator on a different thread
        self.generatorThread = threading.Thread(target=self.threadrun, args=[scale])
        self.generatorThread.daemon = True
        self.generatorThread.start()

    def threadrun(self, scale):
        """
        Start the actual generator thread.
        """
        self.starttime = time.time()
        if self.filename is not None:
            fi = open(self.filename, 'r')
        else:
            fi = None
        while 1:
            nextScheduled = float('inf')
            file_event = None
            if fi is not None:
                line = fi.readline()
                if line == "":
                    fi.close()
                    fi = None
                else:
                    event = line.split(" ", 1)
                    if len(event) != 2:
                        raise DEVSException("Inproperly formatted input in realtime input file: %s" % event)
                    nextScheduled = float(event[0])
                    file_event = event[1][:-1]
            while 1:
                polltime = min(1, (nextScheduled * scale) - (time.time() - self.starttime))
                if polltime > 0:
                    i, _, _ = select.select([sys.stdin], [], [], polltime) 
                else:
                    i = []
                if len(i) > 0:
                    # OK, there was input on stdin before the scheduled time
                    # process it without looking at the file inputs
                    result = sys.stdin.readline()[:-1]
                    self.backend.interrupt(result)
                elif (nextScheduled * scale) - (time.time() - self.starttime) <= 0:
                    # The file provides the next event
                    self.backend.interrupt(file_event)
                    # Break from the inner loop, thus reading the next line in the file
                    break
