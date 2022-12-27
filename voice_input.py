import speech_recognition as sr
from glados import tts
from assistant import query, setup, shutdown

setup()
r = sr.Recognizer()

while(True):
    
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.2)
        audio = r.listen(source)
        text = r.recognize_google(audio, show_all=False)
        print(text)
        
        # answer = query(text)
        # tts(answer)

