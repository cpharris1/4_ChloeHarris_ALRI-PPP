# Capture a few seconds of audio and save to file

import sounddevice as sd
from scipy.io import wavfile
from scipy.io.wavfile import write

# Main Script
fs = 48000
seconds = 5
print("Start recording")
recording = sd.rec(int(seconds*fs), samplerate=fs, channels=2)
sd.wait()

filename = "test-audio.wav"
folder = "audio"
filepath = folder + "/" + filename

print("Stop recording, save to file")
write(filepath, fs, recording)