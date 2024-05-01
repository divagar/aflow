import os
import time
import argparse
import subprocess
from ws4py.client.threadedclient import WebSocketClient

parser = argparse.ArgumentParser(
    description="Audio stream over WebSocket. Two mode of operation: 1. Realtime streaming from sound card 2. Offline streaming from audio file")

parser.add_argument("--host", default="127.0.0.1",
                    help="WebSocket server host")
parser.add_argument("--port", default=9000, type=int,
                    help="WebSocket server port")
parser.add_argument("--bitrate", default=128, type=int,
                    help="Audio bitrate in kbps")
parser.add_argument(
    "--mode", choices=["offline", "realtime"], default="offline", help="Streaming mode")
parser.add_argument("--file", default="./assets/sample.mp3",
                    help="Audio file to stream in offline mode")
parser.add_argument("--card", default=None, help="ALSA card number", type=str)
parser.add_argument("--device", default=None,
                    help="ALSA device number", type=str)
args = parser.parse_args()


websocketUrl = f"ws://{args.host}:{args.port}/ws"
bitrate = args.bitrate * 1024  # kbps to bps
# Convert bits to bytes, then get 100ms chunks
chunkSize = (bitrate // 8)
chunkDuration = 1  # 100 ms chunks


def runCommand(command):
    try:
        result = subprocess.run(command, shell=True, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f'An error occurred while running the command: {e.stderr}')
        return None


def getMicCardNumber():
    cmd = "arecord -l | grep -i dmic | awk 'NR==1 {$2=substr($2,1,length($2)-1); print $2}'"
    result = runCommand(cmd)
    return result


def getMicDeviceNumber():
    cmd = "arecord -l | grep -i dmic | awk 'NR==1 {$6=substr($6,1,length($6)-1); print $6}'"
    result = runCommand(cmd)
    return result


# Ensure --file is provided in offline mode
if args.mode == "offline":
    if args.file is None:
        parser.error(
            "--file arguments is required in offline mode")

# Ensure --card and --device are provided in realtime mode
if args.mode == "realtime":
    if args.card is None or args.device is None:
        # try to get the mic card and device id
        args.card = getMicCardNumber()
        args.device = getMicDeviceNumber()
    if args.card is None or args.device is None:
        parser.error(
            "--card and --device arguments are required in realtime mode")


class AFlowPublisher(WebSocketClient):

    def opened(self):
        if args.mode == "offline":
            self.stream_from_file(args.file)
        elif args.mode == "realtime":
            self.stream_from_mic()

    def stream_from_file(self, audioFilename):
        if audioFilename.endswith((".mp3", ".wav")):
            # Read file size to calculate total chunks once
            fileSize = os.path.getsize(audioFilename)
            totalChunks = (fileSize + chunkSize - 1) // chunkSize

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

    def stream_from_mic(self):
        # Arecord command with card and device
        arecord_cmd = [
            'arecord',
            '--duration=30',
            '--format=s32_le',
            '--rate=48000',
            '--channels=4',
            f'--device=hw:{args.card},{args.device}'
        ]

        # Start the arecord process
        arecord_process = subprocess.Popen(arecord_cmd, stdout=subprocess.PIPE)

        try:
            while True:
                audioChunk = arecord_process.stdout.read(chunkSize)
                if not audioChunk:
                    break
                self.send(audioChunk, binary=True)
                # No need to sleep since arecord will output at the recording rate
        except Exception as e:
            print(e)
        finally:
            arecord_process.kill()

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
