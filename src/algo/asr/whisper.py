import io
import asyncio
import librosa
import soundfile as sf
import numpy as np

import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from datasets import load_dataset
from evaluate import load

# load model and processor
processor = WhisperProcessor.from_pretrained("openai/whisper-tiny.en")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny.en")

async def asr(chunkId, data):
    ret = None
    try:
        print(f"--- {chunkId} | Attempting ASR using Whisper tiny model ---")

        adata = io.BytesIO(data)
        data, sr = sf.read(adata)

        # Reading audio files using PySoundFile is similmar to the method in librosa.
        # One important difference is that the read data is of shape (nb_samples, nb_channels)
        # compared to (nb_channels, nb_samples) in <librosa.core.load>.
        data = data.T

        # covert to mono channel
        audio = librosa.to_mono(data)

        # Resample a time series from orig_sr to target_sr
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

        # input features    
        features = processor(audio, sampling_rate=16000, return_tensors="pt").input_features

        # generate token ids
        predictedIds = model.generate(features)

        # decode token ids to text
        # transcription = processor.batch_decode(predictedIds, skip_special_tokens=False)
        # print(transcription)
        transcription = processor.batch_decode(predictedIds, skip_special_tokens=True)
        if len(transcription) != 0:
            ret = transcription[0]
    except Exception as e:
        print("Error occured while generating ASR")
        print(str(e))
        ret = None
    finally:
        print(f"ASR : {ret}")
        return ret

