#!/usr/bin/python

import SocketServer
import json
import sys

class MyTCPServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True

class MyTCPServerHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            data = json.loads(self.request.recv(1024).strip())
            # process the data, i.e. print it:
            print data
            data[1] = 3
            # send some 'ok' back
            self.request.sendall(json.dumps(data))
        except Exception, e:
            print "Exception wile receiving message: ", e

(ip, port) = (sys.argv[1],sys.argv[2])
server = MyTCPServer((ip, int(port)), MyTCPServerHandler)
server.serve_forever()
