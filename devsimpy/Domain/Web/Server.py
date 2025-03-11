# -*- coding: utf-8 -*-

import Pyro4
import threading

Pyro4.config.COMMTIMEOUT = 1.0 # without this daemon.close() hangs

class Server():
    def __init__(self, port, interface, id):
        """Constructor
        """ 

        self._port= port
        self._interface = interface
        self._id = id

        self.running = False
        
    def enable(self):
        if not self.running:
            self.daemon = Pyro4.Daemon(port=self._port)
            self.daemon.register(self._interface, self._id)

            print("Started thread")
            self.daemon.requestLoop(loopCondition=self.checkshutdown)
           
            self.running = True

    def disable(self):
        print("Called for daemon shutdown")
        self.daemon.close()
        #self.daemon.shutdown()

    def checkshutdown(self):
        return self._interface.running

    def daemonLoop(self, stop):
        self.daemon.requestLoop(loopCondition=self.checkshutdown)
        print("Daemon has shut down no prob")

## We kick off our server
if __name__ == '__main__':

    @Pyro4.expose
    @Pyro4.behavior(instance_mode="single")
    class Interface(object):
        def send(self, data):
            res = "I'm DEVS model that received from web server %s!!"%(str(data))
            #WebGenerator.OUT = data
            return res

    # Run Pyro server in order to send message from web to DEVS atomic models
    s = Server(53546, Interface, "from_web", True)
    s.enable()

    ### if CTRL+C, we kill the aiohttp server and shutdown the Pyro thread!
    try:
        while True:
            pass
    except KeyboardInterrupt as info:
        if s:
            s.setStop(True)
            s.disable()
            s.thread.join()