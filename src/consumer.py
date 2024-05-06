import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
import random
import asyncio
import threading

from algo.silence.silence import isSilent
from algo.noise.noise import isNoisy
from algo.asr.whisper import asr

audioFilename = "/tmp/"
websocketHost = "0.0.0.0"
websocketPort = 9000
cherrypy.config.update(
    {'server.socket_host': websocketHost,   'server.socket_port': websocketPort})


# Start a new event loop in a background thread
# def startBackgroundLoop(loop):
#     asyncio.set_event_loop(loop)
#     loop.run_forever()

# loop = asyncio.new_event_loop()
# t = threading.Thread(target=startBackgroundLoop, args=(loop,), daemon=True)
# t.start()

class AudioWebSocket(WebSocket):
    
    def received_message(self, message):
        # Since this is not an async method, use asyncio.run to call an async method
        asyncio.run(self.handleMessage(message))
        
    async def handleMessage(self, message):
        print(f"Received message")
        if message.is_binary:
            data = message.data
            
            # Run async tasks
            tasks = [
                asyncio.create_task(self.storageAudioChunks(data)),
                asyncio.create_task(self.checkSilence(data)),
                asyncio.create_task(self.checkNoise(data)),
                asyncio.create_task(self.generateSpeech(data))
            ]
            # Await all tasks to complete
            await asyncio.gather(*tasks)

    async def storageAudioChunks(self, data):
        count = random.randint(0, 200)
        fName = audioFilename + "out_" + str(count) + ".mp3"
        with open(fName, "ab") as audioFile:
            audioFile.write(data)
            
    async def checkSilence(self, data):
        # The isSilent function must be an awaitable coroutine
        return await isSilent(data)

    async def checkNoise(self, data):
        # The isNoisy function must be an awaitable coroutine
        return await isNoisy(data)

    async def generateSpeech(self, data):
        # The asr function must be an awaitable coroutine
        return await asr(data)

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
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()
