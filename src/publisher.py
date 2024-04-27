import os
import time
from ws4py.client.threadedclient import WebSocketClient

audioFilename = "./assets/sample.mp3"
websocketHost = "127.0.0.1"
websocketPort = 9000
websocketUrl = f"ws://{websocketHost}:{websocketPort}/ws"
bitRate = 128 * 1024  # 128 kbps in bps
chunkSize = (bitRate // 8)  # Convert bits to bytes
chunkDuration = 1   # one second chunks

# Read file size to calculate total chunks once
fileSize = os.path.getsize(audioFilename)
totalChunks = (fileSize + chunkSize - 1) // chunkSize


class AFlowPublisher(WebSocketClient):

    def opened(self):
        if audioFilename.endswith((".mp3", ".wav")):
            with open(audioFilename, "rb") as audioFile:
                print(f"Opened connection, starting to send audio file")

                for currentChunk in range(totalChunks):
                    startTime = time.time()
                    audioChunk = audioFile.read(chunkSize)
                    print(
                        f"Sending audio chunk : {currentChunk} / {totalChunks} of size {chunkSize}")
                    self.send(audioChunk, binary=True)

                    # sleep to maintain the bitrate
                    timeToSleep = chunkDuration - (time.time() - startTime)
                    print(f"sleep for a while : {timeToSleep} secs")
                    if timeToSleep > 0:
                        time.sleep(timeToSleep)

        else:
            print(f"Only MP3 and WAV file are supported")

    def closed(self, code, reason=None):
        print(f"Closed connection with code: {code}, reason: {reason}")

    def received_message(self, message):
        print(f"Received a message.")


if __name__ == '__main__':
    try:
        ws = AFlowPublisher(websocketUrl)
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
