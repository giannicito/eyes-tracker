from gtts import gTTS

tts = gTTS(text="HELLO WORLD", lang="en")
path = "audio/test.mp3"
tts.save(path)