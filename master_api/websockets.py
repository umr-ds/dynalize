'''
Created on 12.04.2015

@author: PUM
'''
import cherrypy
import log
from ws4py.websocket import WebSocket

logger = log.setup_logger(__name__)

_subscribers = set()

# based on www.ralph-heinkel.com/blog/2012/07/22/publish-subscribe-with-web-sockets-in-python-and-firefox/
class WebSocketMessagePublisher(WebSocket):
    def __init__(self, *args, **kwargs):
        WebSocket.__init__(self, *args, **kwargs)
        _subscribers.add(self)

    def closed(self, *args, **kwargs):
        _subscribers.remove(self)

class WebSocketRoot():
    @cherrypy.expose
    def index(self):
        "Method must exist to serve as a exposed hook for the websocket"

    @cherrypy.expose
    def notify(self, msg):
        for conn in _subscribers:
            try:
                conn.send(msg)
            except Exception as ex:
                conn.close()
                logger.error(ex)

websocket_root = WebSocketRoot()
log.log_observer.set_websocket_root(websocket_root)
