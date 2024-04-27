import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket

websocketHost = "127.0.0.1"
websocketPort = 9000
cherrypy.config.update({'server.socket_port': websocketPort})

class AudioWebSocket(WebSocket):
    def received_message(self, message):
        # Assuming binary audio data
        # Since this is an echo server, we'll just send the data back
        print(f"Received message, is binary: {message.is_binary}")
        if message.is_binary:
            self.send(message.data)


class Root(object):
    @cherrypy.expose
    def index(self):
        return "WebSocket server is running..."

    @cherrypy.expose
    def ws(self):
        """Method must exist to serve as a 'target' for the WebSocket"""
        handler = cherrypy.request.ws_handler


# Register the WebSocket tool
cherrypy.tools.websocket = WebSocketTool()

# Register the WebSocket plugin
WebSocketPlugin(cherrypy.engine).subscribe()

# Map the 'ws' route to the WebSocket
cherrypy.tree.mount(Root(), '/', config={
    '/ws': {
        'tools.websocket.on': True,
        'tools.websocket.handler_cls': AudioWebSocket
    }
})

if __name__ == '__main__':
    cherrypy.engine.start()
    cherrypy.engine.block()
