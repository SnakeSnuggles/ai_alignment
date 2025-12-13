import pyttsx3

def speak(message, vol = 1.0):
    engine = pyttsx3.init()
    engine.setProperty('volume', vol)
    engine.say(message)
    engine.runAndWait()
