import io
import librosa
import soundfile as sf
import numpy as np

noise_threshold_dB = -100.0


def isNoisy(data):
    ret = False
    try:
        print("Checking noise in the audio data")
        adata = io.BytesIO(data)
        data, sr = sf.read(adata)

        # Reading audio files using PySoundFile is similmar to the method in librosa.
        # One important difference is that the read data is of shape (nb_samples, nb_channels)
        # compared to (nb_channels, nb_samples) in <librosa.core.load>.
        data = data.T

        # compute stft and amplitude to db
        data = librosa.to_mono(data)

        # Compute the Short-time Fourier Transform (STFT)
        stft = librosa.stft(data)

        # Convert to amplitude
        amplitude = librosa.amplitude_to_db(np.abs(stft), ref=np.max)
        #print(f"amplitude = {amplitude}")

        # Assuming noise is present where the amplitude is below the threshold
        noiseFrames = np.any(amplitude < noise_threshold_dB, axis=0)

        # Detect sections of noise
        noiseSegments = librosa.frames_to_time(np.where(noiseFrames), sr=sr)

        # Print detected noise segments
        if noiseSegments.size > 0:
            print(f"Noise detected at {noiseSegments} seconds")
            ret = True
        else:
            print("No significant noise detected in the audio data")
            ret = False

    except Exception as e:
        print("Error occured when checking for noise in audio data")
        print(str(e))
        ret = False
    finally:
        print(f"Is noisy ? {ret}")
        return ret
