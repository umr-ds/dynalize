'''
Created on 02.03.2015

@author: PUM
'''
import config
import cherrypy
import os.path
from flask import Flask
from flask.helpers import send_from_directory
from master_api.v1 import api as api_v1
from flask.templating import render_template
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from master_api.websockets import websocket_root, WebSocketMessagePublisher

app = Flask(config.app_name, template_folder="master_api/templates")

@app.route("/web/", defaults={'path': 'index.htm'})
@app.route("/web/<path:path>")
def send_web(path):
    return render_template(path)

@app.route("/web_static/<path:path>")
def send_web_static(path):
    return send_from_directory('master_api/web_static', path)

def run():
        # Registering different API versions
        app.register_blueprint(api_v1, url_prefix="/v1")

        app.config.update(PROPAGATE_EXCEPTIONS = True)

        # Update config and register the websocket plugin
        cherrypy.config.update({
                                'server.socket_port': config.bind_port,
                                'server.socket_host': config.bind_host
                                })

        WebSocketPlugin(cherrypy.engine).subscribe()
        cherrypy.tools.websocket = WebSocketTool()

        # Register flask as wsgi callable in cherrypy
        cherrypy.tree.graft(app, '/')

        # Register WebSocket
        cherrypy.tree.mount(websocket_root, '/ws', config={'/':
                                                           {'tools.websocket.on': True,
                                                            'tools.websocket.handler_cls': WebSocketMessagePublisher
                                                            }
                                                           }
                            )

        if os.path.isfile("cert.pem") and os.path.isfile("privatekey.pem"):
            cherrypy.server.ssl_module = "builtin"
            cherrypy.server.ssl_certificate = "cert.pem"
            cherrypy.server.ssl_private_key = "privatekey.pem"


        # Start cherrypy
        cherrypy.engine.start()
        cherrypy.engine.block()


        # Flask development server start
        #app.run(config.bind_host, config.bind_port, False)
