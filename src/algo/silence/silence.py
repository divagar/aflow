import io
import asyncio
import librosa
import soundfile as sf
import numpy as np


async def isSilent(data):
    ret = False
    try:
        print("--- Checking silence in the audio data ---")
        adata = io.BytesIO(data)
        data, sr = sf.read(adata)

        # Reading audio files using PySoundFile is similmar to the method in librosa.
        # One important difference is that the read data is of shape (nb_samples, nb_channels)
        # compared to (nb_channels, nb_samples) in <librosa.core.load>.
        data = data.T

        # compute stft and amplitude to db
        data = librosa.to_mono(data)
        #data = librosa.resample(data, sr, 16000)
        s = np.abs(librosa.stft(data))
        sDB = librosa.amplitude_to_db(s)

        # Compute A-weighting and add to db value
        freqs = librosa.fft_frequencies(sr=sr)
        aWeights = librosa.A_weighting(freqs)
        aWeights = np.expand_dims(aWeights, axis=1)
        sDBa = sDB + aWeights

        # extract rms feature
        energy = librosa.feature.rms(S=librosa.db_to_amplitude(sDBa))

        # print(energy)
        #print(np.min(energy), np.max(energy))
        ret = np.max(energy) < 0.00001
    except Exception as e:
        print("Error occured when checking for silence in audio data")
        print(str(e))
        ret = False
    finally:
        print(f"Is silent ? {ret}")
        return ret
