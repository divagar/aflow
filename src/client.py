import time
from ws4py.client.threadedclient import WebSocketClient
audioFilename = "./assets/sample.mp3"
websocketHost = "127.0.0.1"
websocketPort = 9000
websocketUrl = "ws://" + websocketHost + ":" + str(websocketPort) + "/ws"


class AudioFileClient(WebSocketClient):
    def opened(self):

        with open(audioFilename, "rb") as audioFile:
            print(f"Opened connection, starting to send audio file")
            chunkSize = 1024
            audioChuck = audioFile.read(chunkSize)
            while audioChuck:
                print(f"Sending audio chuck")
                self.send(audioChuck, binary=True)
                audioChuck = audioFile.read(chunkSize)
                time.sleep(0.1)  # sleep for n/w time taken to send data

    def closed(self, code, reason=None):
        print(f"Closed connection with code: {code}, reason: {reason}")

    def received_message(self, message):
        print(f"Received a message.")


if __name__ == '__main__':
    try:
        ws = AudioFileClient(websocketUrl)
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
