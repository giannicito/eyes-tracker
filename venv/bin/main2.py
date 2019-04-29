from gtts import gTTS
from tempfile import TemporaryFile
from pygame import mixer

tts = gTTS(text='Good morning', lang='en')
mixer.init()

sf = TemporaryFile()
tts.write_to_fp(sf)
sf.seek(0)

mixer.music.load(sf)
mixer.music.set_volume(100)
mixer.music.play()