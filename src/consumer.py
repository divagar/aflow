import random
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket
from pathlib import Path

# Assuming your functions are adapted for async
from algo.silence.silence import isSilent
from algo.noise.noise import isNoisy
from algo.asr.whisper import asr

app = FastAPI()

audioFilename = Path("/tmp/")
websocketHost = "0.0.0.0"
websocketPort = 9000

async def storageAudioChunks(data):
    count = random.randint(0, 200)
    audioFile = audioFilename / f"out_{count}.mp3"
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, writeFile, audioFile, data)

def writeFile(audioFile, data):
    with open(audioFile, "ab") as audioFile:
        audioFile.write(data)

# Define a WS endpoint
@app.websocket("/ws")
async def wsEndpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Get data
            data = await websocket.receive_bytes()
            
            # Run async tasks concurrently
            tasks = [
                asyncio.create_task(storageAudioChunks(data)),
                asyncio.create_task(isSilent(data)),
                asyncio.create_task(isNoisy(data)),
                asyncio.create_task(asr(data))
            ]
            
            # Await all tasks to complete
            results = await asyncio.gather(*tasks)
          
    except Exception as e:
        print(f"WebSocket connection closed with error: {e}")
    finally:
        await websocket.close()

# Define a root endpoint for HTTP for basic response
@app.get("/")
def root():
    return {"message": "WebSocket server is ready to receive audio stream at ws://{host}:{port}/ws".format(host=websocketHost, port=websocketPort)}

if __name__ == "__main__":
    uvicorn.run(app, host=websocketHost, port=websocketPort)