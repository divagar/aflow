import os
import time
import wave
from ws4py.client.threadedclient import WebSocketClient

audioFilename = "./assets/sample.mp3"
websocketHost = "127.0.0.1"
websocketPort = 9000
websocketUrl = "ws://" + websocketHost + ":" + str(websocketPort) + "/ws"
bitRate = 1024 * 128  # 128 Kbps bits per second
chunkSize = bitRate // 8  # Convert bits to bytes
chunkDuration = 1   # one second chunks


class AFlowPublisher(WebSocketClient):

    def opened(self):
        if(".mp3" in audioFilename or ".wav" in audioFilename):
            with open(audioFilename, "rb") as audioFile:
                print(f"Opened connection, starting to send audio file")

                totalChunks = self.getTotalChunk()
                print(f"Total chunks ", totalChunks)

                audioChunk = audioFile.read(chunkSize)
                currentChunk = 1
                while audioChunk:
                    print(
                        f"Sending audio chunk | {currentChunk} / {totalChunks} of size {chunkSize}")
                    startTime = time.time()
                    self.send(audioChunk, binary=True)
                    audioChunk = audioFile.read(chunkSize)

                    # sleep to maintain the bitrate
                    timeToSleep = chunkDuration - (time.time() - startTime)
                    print(f"sleep for a while | {timeToSleep}")
                    if timeToSleep > 0:
                        time.sleep(timeToSleep)

                    # keep track of the current chunk
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
