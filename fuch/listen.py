# fuch/listen.py
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
DURATION = 5  # seconds

model = WhisperModel("small", device="cpu", compute_type="int8")

def listen():
    print("🎤 Listening...")
    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype=np.float32
    )
    sd.wait()

    segments, _ = model.transcribe(audio.flatten(), language="en")
    text = " ".join(seg.text for seg in segments).strip()

    print(f"🗣️ You said: {text}")
    return text
