import os
import time
import wave
from ws4py.client.threadedclient import WebSocketClient

audioFilename = "./assets/sample.mp3"
websocketHost = "127.0.0.1"
websocketPort = 9000
websocketUrl = "ws://" + websocketHost + ":" + str(websocketPort) + "/ws"
chunkSize = 1024 * 128  # 128 Kbps


class AFlowPublisher(WebSocketClient):

    def opened(self):
        if(".mp3" in audioFilename or ".wav" in audioFilename):
            with open(audioFilename, "rb") as audioFile:
                print(f"Opened connection, starting to send audio file")

                totalChunks = self.getTotalChunk()
                print(f"Computing total chunks ", totalChunks)

                audioChunk = audioFile.read(chunkSize)
                currentChunk = 1
                while audioChunk:
                    print(
                        f"Sending audio chunk {currentChunk} / {totalChunks} of size {chunkSize}")
                    self.send(audioChunk, binary=True)
                    audioChunk = audioFile.read(chunkSize)
                    time.sleep(0.1)  # sleep for n/w time taken to send data
                    currentChunk += 1
        else:
            print(f"Only MP3 and WAV file are supported")

    def closed(self, code, reason=None):
        print(f"Closed connection with code: {code}, reason: {reason}")

    def received_message(self, message):
        print(f"Received a message.")

    def getTotalChunk(self):
        totalChunks = 0
        fileSize = os.path.getsize(audioFilename)

        while fileSize > 0:
            totalChunks += 1
            #totalChunkSize += chunkSize
            fileSize -= chunkSize
        return totalChunks


if __name__ == '__main__':
    try:
        ws = AFlowPublisher(websocketUrl)
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
