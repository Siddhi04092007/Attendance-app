import numpy as np

def rms_level(audio):
    """Normalized RMS amplitude; activity level only, not speech recognition."""
    if audio is None:
        return 0.0
    data = np.asarray(audio, dtype=np.float32)
    if data.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(data))))

def capture_rms(seconds=2, sample_rate=16000):
    """Optional microphone sample; requires sounddevice and OS permission."""
    import sounddevice as sd
    audio = sd.rec(int(seconds * sample_rate), samplerate=sample_rate,
                   channels=1, dtype="float32")
    sd.wait()
    return rms_level(audio)
