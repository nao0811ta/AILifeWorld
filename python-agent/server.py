# -*- coding: utf-8 -*-

import cherrypy
import argparse
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
import msgpack

from agent import Agent

from datetime import datetime
import pickle
import atexit

parser = argparse.ArgumentParser(description='ml-agent-for-unity')
parser.add_argument('--port', '-p', default='8765', type=int,
                    help='websocket port')
parser.add_argument('--ip', '-i', default='0.0.0.0',
                    help='server ip')
parser.add_argument('--gpu', '-g', default=-1, type=int,
                    help='GPU ID (negative value indicates CPU)')
parser.add_argument('--log-file', '-l', default='reward.log', type=str,
                    help='reward log file name')
parser.add_argument('--model', '-m', default='', type=str,
                    help='model trained')

args = parser.parse_args()


def save(obj):
    backup_name = datetime.now().strftime("%Y%m%d%H%M%S") + '.dump'
    print 'backed up ' + backup_name
    with open(backup_name, 'wb') as f:
        pickle.dump(obj, f)
        f.close()


def load(backupPath):
    print 'loaded ' + backupPath
    with open(backupPath, 'rb') as f:
        a = pickle.load(f)
        f.close()
        return a


if not args.model:
    agent = Agent(args)
else:
    agent = load(args.model)

atexit.register(save, obj=agent)


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
    def send_action(self, action):
        dat = msgpack.packb({"c0": str(action[0][0]), "c1": str(action[0][1])})
        self.send(dat, binary=True)

    def received_message(self, m):
        payload = m.data
        dat = msgpack.unpackb(payload)
        agent.received_message(self, dat)


cherrypy.config.update({'server.socket_host': args.ip,
                        'server.socket_port': args.port})
WebSocketPlugin(cherrypy.engine).subscribe()
cherrypy.tools.websocket = WebSocketTool()
cherrypy.config.update({'engine.autoreload.on': False})
config = {'/ws': {'tools.websocket.on': True,
                  'tools.websocket.handler_cls': AgentServer}}
cherrypy.quickstart(Root(), '/', config)
