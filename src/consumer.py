import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
import random

from algo.silence import isSilent

audioFilename = "/tmp/"
websocketHost = "0.0.0.0"
websocketPort = 9000
cherrypy.config.update(
    {'server.socket_host': websocketHost,   'server.socket_port': websocketPort})



class AudioWebSocket(WebSocket):
    def received_message(self, message):
        count = random.randint(0, 200)
        print(f"Received message {count}")
        if message.is_binary:
            fName = audioFilename + "out_" + str(count) + ".mp3"
            with open(fName, "ab") as audio_file:
                audio_file.write(message.data)
                # check silence
                isSilent(message.data)
        count += 1


class Root(object):
    @cherrypy.expose
    def index(self):
        return f"WebSocket server is ready to receive audio stream at ws://{websocketHost}:{websocketPort}/ws"

    @cherrypy.expose
    def ws(self):
        # WebSocket endpoint
        pass


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
