from .cores import *
import threading

class AsynchronousComboGenerator:
    def __init__(self, filename, core = PythonThreads):
        self.prevtime = 0
        self.filename = filename
        self.core = core

    def startFileInput(self):
        if self.filename != None:
            fi = open(self.filename, 'r')
            while True:
                line = fi.readline()
                if line == "":
                    # File input is finished, though user input might still be pending
                    break
                event = line.split()
                if len(event) == 3:
                    transtime, port, data = event
                    result = str(port) + " " + str(data)
                else:
                    print(("Inproperly formatted input: " + str(line)))
                    break
                self.core.scheduleAfter(transtime, self.recv.performExtTransition, [result])

    def run(self):
        result = None
        while result != "":
            print("Input (empty or invalid input to exit): ")
            result = input()
            # First perform a sanity check on the input
            try:
                (a, b) = result.split()
            except:
                if result != "":
                    print("ERROR: input should be of the form PORT VALUE, exiting!")
                result = ""
            self.core.scheduleAfter(0, self.recv.performExtTransition, [result])

    def setReceiver(self, recv):
        self.recv = recv
