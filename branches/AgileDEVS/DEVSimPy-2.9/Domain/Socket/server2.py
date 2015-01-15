#!/usr/bin/python

import SocketServer
import json
import sys

class MyTCPServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True

class MyTCPServerHandler(SocketServer.BaseRequestHandler):
    buf={}
    def handle(self):
        try:
            
            data = json.loads(self.request.recv(1024).strip())
            # process the data, i.e. print it:
            print data
            value, time = data
            if value=='GET':
              out=MyTCPServerHandler.buf.get(float(time),None)
              data=out
            else:
              MyTCPServerHandler.buf[time]=value
            # send some 'ok' back
            self.request.sendall(json.dumps(data))
        except Exception, e:
            print "Exception wile receiving message: ", e
        print MyTCPServerHandler.buf

#(ip, port) = (sys.argv[1],sys.argv[2])
#server = MyTCPServer((ip, int(port)), MyTCPServerHandler)
server = MyTCPServer(('localhost', 9090), MyTCPServerHandler)
server.serve_forever()

