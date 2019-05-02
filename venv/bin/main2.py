from gtts import gTTS
from playsound import playsound

tts = gTTS(text='HELLO GIANNI', lang='en')
tts.save("audio/test.mp3")

playsound("audio/test.mp3")