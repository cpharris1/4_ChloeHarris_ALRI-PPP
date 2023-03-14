

# ==============================================================
# Imports
# ==============================================================

# Kivy GUI
#from kivy.config import Config
#Config.set('graphics','resizable',True)
#Config.set('graphics','fullscreen',1)
#import os
#os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

#from kivy.core.window import Window
#Window.maximize()
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy_garden.graph import Graph
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('tkagg') # RaspPi specific backend
import matplotlib.pyplot as plt
from kivy.uix.screenmanager import ScreenManager, Screen

import time
import datetime
import sounddevice as sd
from scipy.io import wavfile
from scipy.io.wavfile import write
import serial

# importing mdapp from kivymd framework
from kivymd.app import MDApp

# ==============================================================
# Start-up
# ==============================================================

from kivy.config import Config 
Config.set('graphics', 'width', '800') 
Config.set('graphics', 'height', '400')

# ser = serial.Serial(
#     #"/dev/serial0", # RPi port
#     "COM7", # Windows port
#     baudrate=115200,
#     bytesize=serial.EIGHTBITS,
#     parity=serial.PARITY_NONE,  # PARITY_EVEN & ODD have issues
#     stopbits=serial.STOPBITS_ONE,
#     timeout=1,
# )
# ser.reset_input_buffer()

# ==============================================================
# Functions
# ==============================================================

def ser_writeread(msg_out):
    # Expects a message to send and returns 1-line response
    ser.write(msg_out.encode("utf-8"))
    print("> " + msg_out)  # Print statement for testing
    while True:
        # waits for response and returns message
        if ser.in_waiting > 0:
            msg_in = ser.readline().decode("utf-8").rstrip()
            print("< " + msg_in)  # Print statement for testing
            break
    return msg_in
def ser_readBIOZ():
    # Using readlines(), read until timeout triggers EOF
    # NOTE: This could be buggy, if so swap to hardcoded stop
    # Return the filestamp for later reading
    while True:
        if ser.in_waiting > 0:
            msg_in = ser.readline().decode("utf-8").rstrip()
            print("< " + msg_in)
            if msg_in == "Measurements start":
                # End of print block, exit loop
                break
    #timestamp = str(datetime.datetime.today())
    #timestamp = timestamp.replace(" ", "_").replace(":","-")
    #filepath = "bioz/" + timestamp + ".csv"
    
    filename = "test-bioz.csv"
    folder = "bioz"
    filepath = folder + "/" + filename
    fileHandler = open(filepath, "w")
    while True:
        if ser.in_waiting > 0:
            msg_in = ser.readline().decode("utf-8").rstrip()
            print("< " + msg_in)
            if msg_in == "Measurements done":
                # End of print block, exit loop
                break
            else:
                # Valid data, print to file
                fileHandler.write(msg_in + "\n")
    fileHandler.close()
    return filepath

# ==============================================================
# Main GUI objects
# ==============================================================

class biozPopup(BoxLayout):
    pass

class audioPopup(BoxLayout):
    pass

class MenuScreen(Screen):
    pass

class BiozScreen1(Screen):
    pass

class AudioScreen1(Screen):
    pass

class Main(MDApp):
    pt_id = "1"
    cl_id = "1"
    def get_bioz(self):
        ser.reset_input_buffer()
        ser_writeread("START")
        ser_readBIOZ()

    def plot_bioz(self):
        savedFile = "bioz/test-bioz.csv"
        print("Creating figure from measurements")
        fig, (ax1, ax2) = plt.subplots(2,1)

        # Add resistance subplot
        df = pd.read_csv(savedFile)     # Read csv file into DataFrame object
        #df = df.drop('ResistanceRaw',axis=1) # Drop RawValues column from object
        df = df.pivot_table(index='Frequency',
                            columns='MeasNumber',
                            values='ResistanceComputed',
                            aggfunc='mean')
            # Convert dataframe to pivot table
        print(df)   # Print pivot table to terminal to confirm values
        df.plot(ax=ax1, legend=None, logx=True)   # Plot DataFrame object to matplotlib window
        ax1.set_title('Measured Resistance (Ohm)')
        #ax1.axis([0, 128000, 45, 55])

        # Add reactance subplot
        df = pd.read_csv(savedFile)     # Read csv file into DataFrame object
        df = df.pivot_table(  index='Frequency',
                        columns='MeasNumber',
                        values='ReactanceComputed',
                        aggfunc='mean')
            # Convert dataframe to pivot table
        print(df)   # Print pivot table to terminal to confirm values
        df.plot(ax=ax2, legend=None, logx=True)   # Plot DataFrame object to matplotlib window
        ax2.xaxis.set_label_text('Frequency (Hz)')
        ax2.set_title('Measured Reactance (Ohm)')
        #ax2.axis([0, 128000, -5, 5])

        print("Displaying figures to user")
        fig.subplots_adjust(hspace=1.0)
        mng = plt.get_current_fig_manager()
        mng.resize(*mng.window.maxsize())
        mng.window.state('zoomed')
        plt.show()  # Show matplotlib figure
        print("User closed figure, exiting from BIOZ")

    def get_audio(self):
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

    def plot_audio(self):
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
        # plt.ylabel("Amplitude")

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

    def show_bioz(self):
        # Function for displaying a pop-up window with Kivy
        # Unused at this time
        show = biozPopup()
        popupWindow = Popup(title="BIOZ Popup", content=show, size_hint=(0.8,0.8)) 
        popupWindow.open()

    def show_audio(self):
        # Function for displaying a pop-up window with Kivy
        # Unused at this time
        show = audioPopup()
        popupWindow = Popup(title="Audio Popup", content=show, size_hint=(0.8,0.8)) 
        popupWindow.open()

    def new_timestamp(self):
        return datetime.datetime.now().replace(microsecond=0).isoformat()

    # def print_patient_id(self):
    #     print(self.root.ids.patient_id.text)

    timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
    pass

if __name__ == '__main__':
    Main().run()