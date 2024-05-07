import struct
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

async def storageAudioChunks(chunkId, data):
    audioFile = audioFilename / f"out_{chunkId}.mp3"
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, writeFile, audioFile, data)

def writeFile(audioFile, data):
    with open(audioFile, "ab") as audioFile:
        audioFile.write(data)
        
def extractAudioMetaData(data):
    # Simple binary structure to pack audio chunk metadata
    # Metadata Format structure: chunkId (int), chunkSize (int), channels (int), sampleRate (int)
    metadataFormat = '<I I I I'
    metadataSize = struct.calcsize(metadataFormat)
    metadataBytes = data[:metadataSize]
    chunkId, chunkSize, channels, sampleRate = struct.unpack(metadataFormat, metadataBytes)
    
    return metadataSize, chunkId, chunkSize, channels, sampleRate

# Define a WS endpoint
@app.websocket("/ws")
async def wsEndpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Get data
            audioData = await websocket.receive_bytes()
            
            # extract metadata
            metadataSize, chunkId, chunkSize, channels, sampleRate = extractAudioMetaData(audioData)
            print(f"Proccessing Chunk {chunkId} | chunkSize {chunkSize} | channels {channels} | sampleRate {sampleRate}")
            
            # get chunk data
            audioChunk = audioData[metadataSize:]
            
            # Run async tasks concurrently
            tasks = [
                asyncio.create_task(storageAudioChunks(chunkId, audioChunk)),
                asyncio.create_task(isSilent(chunkId, audioChunk)),
                asyncio.create_task(isNoisy(chunkId, audioChunk)),
                asyncio.create_task(asr(chunkId, audioChunk))
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