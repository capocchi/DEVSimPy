import json
import threading
import SocketServer
import traceback

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
        print("reception " + self.data +"\n\r")

        if self.data == "SUSPEND":
            self.server.simulation_thread.suspend()
            #while not self.server.simulation_thread.suspension_applied: TODO? modif Strategy needed
                ###TODO set a timeout and return a NOK status if simulation is not suspended
                #pass
            self.request.send('SUSPENDED')

        elif self.data == "RESUME":
            self.server.simulation_thread.resume_thread()
            #while self.server.simulation_thread.suspension_applied: TODO? modif Strategy needed
                ###TODO set a timeout and return a NOK status if simulation remains suspended
                #pass
            self.request.send('RESUMED')
        else:
            data       = json.loads(self.data)
            modelID    = data['modelID']
            paramName  = data['paramName']
            paramValue = data['paramValue']
            if self.server.simulation_thread.thread_suspend:
                if self.server._componentSet.has_key(modelID):
                    if paramName in dir(self.server._componentSet[modelID]):
                        setattr(self.server._componentSet[modelID], paramName, int(paramValue))
                        # just send back OK
                        self.request.send('OK')
                    else:
                        self.request.send('UNKNOWN_PARAM_NAME')
                else:
                    self.request.send('UNKNOWN_MODELID')
            else:
                self.request.send('SIM_IN_PROGRESS')


#class MySocketServer(SocketServer.UnixStreamServer):
class MySocketServer(SocketServer.TCPServer):

    def __init__(self, server_address, RequestHandlerClass, simulation_thread):

        #SocketServer.UnixStreamServer.__init__(self, server_address, RequestHandlerClass)
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
        self.simulation_thread = simulation_thread
        self._componentSet = self.simulation_thread.model.getFlatComponentSet()

    def handle_error(self, request, client_address):
        print '-'*40
        print 'Exception happened during processing of request from',
        print client_address
        print(traceback.format_exc())
        print '-'*40

class InteractionManager(threading.Thread):

    def __init__(self, socket_id, simulation_thread):

        threading.Thread.__init__(self)
        print('InteractionManager thread init ')
        try:
            self.server = MySocketServer(('localhost', 5555), MySocketHandler, simulation_thread)
            # UNIX socket server initialization
            #socket_address = '\0' + socket_id
            #self.server = MySocketServer(socket_address, MySocketHandler, simulation_thread)
            print('socket server init ')
        except:
            print ('socket server initialization failed')
            print (traceback.format_exc())

        #self.daemon = True

    def run(self):

        if self.server:
            print('serve_forever ')
            self.server.serve_forever()

    def stop(self):

        if self.server:
            print('server shutdown')
            self.server.shutdown()
            self.server.server_close()
