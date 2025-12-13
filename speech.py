import numpy as np
import speech_recognition as sr
import whisper

r = sr.Recognizer()
model = whisper.load_model("base")

def get_from_microphone():
    with sr.Microphone(sample_rate=16000) as source:
        print("Say something!")
        audio = r.listen(source)
        print("Processing...")

    raw = audio.get_raw_data()
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

    result = model.transcribe(samples, fp16=False)

    return result["text"]

