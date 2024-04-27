import time
from ws4py.client.threadedclient import WebSocketClient


class AudioFileClient(WebSocketClient):
    def opened(self):
        # Let's send the audio file in chunks
        with open("./assets/sample.mp3", "rb") as audio_file:
            # Sending data in small chunks, you can define the chunk size
            chunk_size = 1024
            chunk = audio_file.read(chunk_size)
            while chunk:
                print(f"Sending audio chuck")
                self.send(chunk, binary=True)
                chunk = audio_file.read(chunk_size)
                time.sleep(0.1)  # Just to simulate time taken to send data

    def closed(self, code, reason=None):
        print(f"Closed down with code: {code}, reason: {reason}")

    def received_message(self, message):
        print(f"Received a message, but this client doesn't do anything with it.")


if __name__ == '__main__':
    try:
        ws = AudioFileClient('ws://127.0.0.1:8765/ws',
                             protocols=['http-only', 'chat'])
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
