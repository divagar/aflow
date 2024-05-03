import os
import time
import struct
import wave
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
parser.add_argument("--file", default="./assets/sample.wav",
                    help="Audio file to stream in offline mode")
parser.add_argument("--card", default=None, help="ALSA card number", type=str)
parser.add_argument("--device", default=None,
                    help="ALSA device number", type=str)
args = parser.parse_args()

# General configs
websocketUrl = f"ws://{args.host}:{args.port}/ws"
mode = args.mode
audioChunkDuration = 1  # 100 ms chunks
audioChunkLengthInSecs = 2  # 2secs chunks

# Configs for realtime mode
audioCardNumber = args.card
audioDeviceNumber = args.device
audioRecordDuration = 30
audioFormat = "s32_le"
audioSampleRate = 48000
audioSampleWidth = None
audioChannels = 4

# Configs for offline mode
audioFileName = args.file

# bitrate = args.bitrate * 1024  # kbps to bps
# Convert bits to bytes, then get 100ms chunks
# chunkSize = (bitrate // 8)


def runCommand(command):
    try:
        result = subprocess.run(command, shell=True, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f'An error occurred while running the command: {e.stderr}')
        return None


def getRecoderCardNumber():
    cmd = "arecord -l | grep -i dmic | awk 'NR==1 {for(i=1;i<=NF;i++) if($i==\"card\") {$(i+1)=substr($(i+1),1,length($(i+1))-1); print $(i+1)}}'"
    result = runCommand(cmd)
    return result


def getRecoderDeviceNumber():
    cmd = "arecord -l | grep -i dmic | awk 'NR==1 {for(i=1;i<=NF;i++) if($i==\"device\") {$(i+1)=substr($(i+1),1,length($(i+1))-1); print $(i+1)}}'"
    result = runCommand(cmd)
    return result


def isWAVFile(file):
    try:
        with wave.open(file, 'rb') as f:
            return True
    except wave.Error as e:
        return False
    except FileNotFoundError:
        return False


def readWavFileHeader(file):
    with wave.open(file, 'rb') as wf:
        channels = wf.getnchannels()
        sampleRate = wf.getframerate()
        bitsPerSample = wf.getsampwidth() * 8
        totalDataSize = wf.getnframes() * channels * (bitsPerSample // 8)
        print(f"wf.getnframes()= {wf.getnframes()}")

    return channels, sampleRate, bitsPerSample, totalDataSize


def generateWavFileHeader(channels, sampleRate, bitsPerSample, numOfFrames):
    bytes_per_sample = bitsPerSample // 8
    block_align = channels * bytes_per_sample
    byte_rate = sampleRate * block_align
    subchunk2_size = numOfFrames * block_align

    header = (b'RIFF' +
              struct.pack('<I', 36 + subchunk2_size) +
              b'WAVE' +
              b'fmt ' +
              struct.pack('<IHHIIHH', 16, 1, channels, sampleRate, byte_rate, block_align, bitsPerSample) +
              b'data' +
              struct.pack('<I', subchunk2_size))
    return header


# Ensure --file is provided in offline mode
if mode == "offline":
    if audioFileName is None:
        parser.error(
            "--file arguments is required in offline mode")

# Ensure --card and --device are provided in realtime mode
if mode == "realtime":
    if audioCardNumber is None or audioDeviceNumber is None:
        # try to get the mic card and device id
        audioCardNumber = getRecoderCardNumber()
        audioDeviceNumber = getRecoderDeviceNumber()
    if audioCardNumber is None or audioDeviceNumber is None:
        parser.error(
            "--card and --device arguments are required in realtime mode")


class AFlowPublisher(WebSocketClient):

    def opened(self):
        if mode == "offline":
            self.streamViaFile()
        elif mode == "realtime":
            self.streamViaRecoder()

    def closed(self, code, reason=None):
        print(f"Closed connection with code: {code}, reason: {reason}")

    def received_message(self, message):
        print(f"Received a message.")

    def send_message(self, message, count=1):
        print(f"Send a message | count: {count}")
        self.send(message, binary=True)

    def streamViaFile(self):
        if audioFileName.endswith((".wav")) and isWAVFile(audioFileName):

            # get wave header info
            audioChannels, audioSampleRate, audioBitsPerSample, audioTotalDataSize = readWavFileHeader(
                audioFileName)
            print(
                f"audioChannels = {audioChannels} audioSampleRate = {audioSampleRate} audioBitsPerSample = {audioBitsPerSample} audioTotalDataSize = {audioTotalDataSize}")

            # Calculate frame size, frames per chunk and bytes per chunk
            frameSize = audioChannels * (audioBitsPerSample // 8)
            framesPerChunk = audioSampleRate * audioChunkLengthInSecs
            bytesPerChunk = framesPerChunk * frameSize

            with open(audioFileName, "rb") as audioFile:
                print(f"Starting the realtime audio stream via file mode")

                audioFile.seek(44)  # Typical WAV header length

                while audioTotalDataSize > 0:
                    startTime = time.time()
                    chunkSize = min(bytesPerChunk, audioTotalDataSize)
                    audioChunk = audioFile.read(chunkSize)
                    audioTotalDataSize -= chunkSize

                    numsFramesInChunk = len(audioChunk)
                    audioChunkHeader = generateWavFileHeader(
                        audioChannels, audioSampleRate, audioBitsPerSample, numsFramesInChunk)

                    self.send_message(audioChunkHeader + audioChunk)

                    # sleep to maintain the bitrate
                    timeToSleep = audioChunkDuration - \
                        (time.time() - startTime)
                    print(f"sleep for a while : {timeToSleep} secs")
                    if timeToSleep > 0:
                        time.sleep(timeToSleep)
            print(f"End of realtime audio stream via file mode")

        else:
            print(f"Only WAV file are supported")

    def streamViaRecoder(self):
        currentChunk = 1
        arecord_cmd = [
            'arecord',
            '--duration='+str(audioRecordDuration),
            '--format=' + str(audioFormat),
            '--rate=' + str(audioSampleRate),
            '--channels=' + str(audioChannels),
            f'--device=hw:{audioCardNumber},{audioDeviceNumber}'
        ]
        # Start the arecord process
        arecordProcess = subprocess.Popen(arecord_cmd, stdout=subprocess.PIPE)
        try:
            print(f"Starting the realtime audio stream via recoder mode")
            while True:
                audioChunk = arecordProcess.stdout.read(chunkSize)
                if not audioChunk:
                    # end the stream
                    print(f"End of realtime audio stream via recoder mode")
                    break
                # send audio chuck
                self.send_message(audioChunk, currentChunk)
                currentChunk += 1
                # No need to sleep since arecord will output at the recording rate
        except Exception as e:
            print(e)
        finally:
            arecordProcess.kill()


if __name__ == '__main__':
    try:
        ws = AFlowPublisher(websocketUrl)
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
