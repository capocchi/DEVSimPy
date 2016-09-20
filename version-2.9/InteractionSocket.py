# -*- coding: utf-8 -*-

import json
import threading
import SocketServer
import traceback
import sys
from numpy import Infinity

if sys.platform == "win32":
    Server = SocketServer.TCPServer
else:
    Server = SocketServer.UnixStreamServer

def log(s):
    sys.stdout.write(s)

class MySocketHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.
    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def handle(self):
        # request is the socket connected to the client
        self.data = self.request.recv(1024).strip()

        log("*** reception " + self.data)
        response = {}
        
        if self.data == "PAUSE":
            self.server.simulation_thread.suspend()
            #while not self.server.simulation_thread.suspension_applied: pass TODO? modif Strategy needed
            response['status'] = 'PAUSED'

            # Simulation time is not reliable before thread is actually suspended
            # Infinity might be returned
            response['simulation_time'] = self.server.simulation_thread.model.myTimeAdvance
            if response['simulation_time'] == Infinity:
                response['simulation_time'] = 'undefined'

        elif self.data == "RESUME":
            response['simulation_time'] = self.server.simulation_thread.model.myTimeAdvance
            self.server.simulation_thread.resume_thread()
            #while self.server.simulation_thread.suspension_applied:pass TODO? modif Strategy needed
            response['status'] = 'RESUMED'

        else:
            data       = json.loads(self.data)
            model_name = data['block_label']
            params     = data['block']

            if self.server.simulation_thread.thread_suspend:
                response['status'] = 'OK'
                response['simulation_time'] = self.server.simulation_thread.model.myTimeAdvance
                
                if self.server._componentSet.has_key(model_name):

                    for param_name, param_value in params.items() :
                        if param_name in dir(self.server._componentSet[model_name]):                       
                            setattr(self.server._componentSet[model_name], param_name, param_value)
                        else:
                            response['status'] += ' - UNKNOWN_PARAM ' + param_name

                else:
                    response['status'] = 'UNKNOWN_MODEL_NAME ' + model_name
            else:
                response['status'] = 'SIM_NOT_PAUSED'

        self.request.send(json.dumps(response))

class MySocketServer(Server):

    def __init__(self, server_address, RequestHandlerClass, simulation_thread):

        if sys.platform == "win32":
            SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
        else:
            SocketServer.UnixStreamServer.__init__(self, server_address, RequestHandlerClass)

        self.simulation_thread = simulation_thread
        self._componentSet = self.simulation_thread.model.getFlatComponentSet()

    def handle_error(self, request, client_address):
        sys.stderr.write('*** EXCEPTION handling msg in InteractionManager')
        sys.stderr.write(client_address)
        sys.stderr.write(traceback.format_exc())
        sys.stderr.write(' ***')

class InteractionManager(threading.Thread):

    def __init__(self, socket_id, simulation_thread):

        threading.Thread.__init__(self)
        self.daemon = True
        log('SocketServer thread init ** ')
        try:
            # TCP socket server initialization
            #self.server = MySocketServer(('localhost', 5555), MySocketHandler, simulation_thread)

            # UNIX socket server initialization
            self.server = MySocketServer('\0' + socket_id, MySocketHandler, simulation_thread)

            log('SocketServer created ** ')
                
        except:
            self.server = None
            log ('SocketServer creation failed ** ')
            #log (traceback.format_exc())
            raise


    def run(self):

        if self.server:
            log('SocketServer serve_forever ** ')
            self.server.serve_forever()

    def stop(self):

        if self.server:
            log('SocketSserver shutdown')
            self.server.shutdown()
            self.server.server_close()