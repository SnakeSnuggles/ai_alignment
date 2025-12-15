import time
import queue
import threading
import numpy as np
import speech_recognition as sr
import whisper
from snakes_garbage import *

# --------------------
# Setup
# --------------------

r = sr.Recognizer()
model = whisper.load_model("base.en")

audio_queue = queue.Queue(maxsize=20)

# --------------------
# Audio callback (runs on background thread)
# --------------------

def audio_callback(recognizer, audio):
    try:
        audio_queue.put_nowait(audio)
    except queue.Full:
        # Drop audio if Whisper is behind
        pass


