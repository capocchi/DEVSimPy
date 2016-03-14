import json
import threading
import SocketServer
import traceback
import sys

def log (s):
    sys.stderr.write(s)

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
        log("reception " + self.data +"\n\r")

        if self.data == "PAUSE":
            self.server.simulation_thread.suspend()
            #while not self.server.simulation_thread.suspension_applied: pass TODO? modif Strategy needed
            self.request.send('PAUSED')

        elif self.data == "RESUME":
            self.server.simulation_thread.resume_thread()
            #while self.server.simulation_thread.suspension_applied:pass TODO? modif Strategy needed
            self.request.send('RESUMED')

        else:
            data       = json.loads(self.data)
            model_name = data['block_label']
            params     = data['block']
            response   = 'OK'

            if self.server.simulation_thread.thread_suspend:

                if self.server._componentSet.has_key(model_name):

                    for param_name, param_value in params.items() :
                        if param_name in dir(self.server._componentSet[model_name]):
                            setattr(self.server._componentSet[model_name], param_name, int(param_value))
                        else:
                            response += ' - UNKNOWN_PARAM ' + param_name
                    self.request.send(response)
                else:
                    self.request.send('UNKNOWN_MODEL_NAME ' + model_name)
            else:
                self.request.send('SIM_NOT_PAUSED')


class MySocketServer(SocketServer.UnixStreamServer):
#class MySocketServer(SocketServer.TCPServer):

    def __init__(self, server_address, RequestHandlerClass, simulation_thread):

        SocketServer.UnixStreamServer.__init__(self, server_address, RequestHandlerClass)
        #SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
        self.simulation_thread = simulation_thread
        self._componentSet = self.simulation_thread.model.getFlatComponentSet()

    def handle_error(self, request, client_address):
        log('*** EXCEPTION handling msg in InteractionManager')
        log(client_address)
        log(traceback.format_exc())
        log(' ***')

class InteractionManager(threading.Thread):

    def __init__(self, socket_id, simulation_thread):

        threading.Thread.__init__(self)
        self.daemon = True
        log('InteractionManager : thread init ')
        try:
            # TCP socket server initialization
            #self.server = MySocketServer(('localhost', 5555), MySocketHandler, simulation_thread)

            # UNIX socket server initialization
            self.server = MySocketServer('\0' + socket_id, MySocketHandler, simulation_thread)

            log('InteractionManager : socket server created ')
        except:
            self.server = None
            log ('InteractionManager : socket server creation failed')
            #log (traceback.format_exc())
            raise


    def run(self):

        if self.server:
            log('InteractionManager : serve_forever ')
            self.server.serve_forever()

    def stop(self):

        if self.server:
            log('InteractionManager : server shutdown')
            self.server.shutdown()
            self.server.server_close()