# -*- coding: utf-8 -*-

import cherrypy
import argparse
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
import msgpack
from agent import Agent

import threading

parser = argparse.ArgumentParser(description='ml-agent-for-unity')
parser.add_argument('--port', '-p', default='8765', type=int,
                    help='websocket port')
parser.add_argument('--ip', '-i', default='0.0.0.0',
                    help='server ip')
parser.add_argument('--gpu', '-g', default=-1, type=int,
                    help='GPU ID (negative value indicates CPU)')
parser.add_argument('--log-file', '-l', default='reward.log', type=str,
                    help='reward log file name')
args = parser.parse_args()

# Test
class Root(object):
    @cherrypy.expose
    def index(self):
        return 'some HTML with a websocket javascript connection'

    @cherrypy.expose
    def ws(self):
        # you can access the class instance through
        handler = cherrypy.request.ws_handler

class AgentServer(WebSocket):
    thread_event = threading.Event()

    def send_action(self, action):
        dat = msgpack.packb({"command": str(action)})
        self.send(dat, binary=True)

    def send_actionAndgene(self, action, gene): # add Naka, #MUST FIX 0,1,2 -> number of parameter
        dat = msgpack.packb({"command": str(action), "gene1": str(gene[0]), "gene2": str(gene[1]), "gene3": str(gene[2])})
        self.send(dat, binary=True)

    def received_message(self, m):
        print 'received parent'
        payload = m.data
        dat = msgpack.unpackb(payload)
        agent = Agent.Instance(args)
        agent.received_message(dat)

        self.thread_event.set()

cherrypy.config.update({'server.socket_host': args.ip,
                        'server.socket_port': args.port})
WebSocketPlugin(cherrypy.engine).subscribe()
cherrypy.tools.websocket = WebSocketTool()
cherrypy.config.update({'engine.autoreload.on': False})
config = {'/ws': {'tools.websocket.on': True,
                  'tools.websocket.handler_cls': AgentServer}}
cherrypy.quickstart(Root(), '/', config)

