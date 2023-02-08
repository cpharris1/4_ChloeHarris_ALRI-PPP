# Simple script to open and plot audio file
# Can plot in both time or frequency domain
# Execution is halted while figure is open

# Imports
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile


# Main Script
filename = "test-audio.wav"
folder = "audio"
filepath = folder + "/" + filename


sample_rate, audio_data = wavfile.read(filepath)
length = audio_data.shape[0] / sample_rate
time = np.linspace(0, length, audio_data.shape[0])

##  Plot time-domain view of audio      
# plt.figure(1)
# plt.subplot(2, 1, 1)
# plt.plot(time,audio_data[:, 0], label="Left channel")
# plt.legend()
# plt.ylabel("Amplitude")     
# plt.subplot(2, 1, 2)
# plt.plot(time,audio_data[:, 1], label="Right channel")
# plt.legend()
# plt.xlabel("Time [s]")
# plt.ylabel("Amplitude"

##  Plot frequency-domain view
signal = audio_data[:,0] # Extract 1 track from audio
fft_spectrum = np.fft.rfft(signal) # Compute FFT spectrum
freq = np.fft.rfftfreq(signal.size, d=1./sample_rate) # Compute fft frequency units
fft_spectrum_abs = np.abs(fft_spectrum)
plt.figure(1)
plt.plot(freq, fft_spectrum_abs)
plt.xlabel("frequency, Hz")
plt.ylabel("Amplitude, units")
mng = plt.get_current_fig_manager()
mng.window.state('zoomed')
plt.show()