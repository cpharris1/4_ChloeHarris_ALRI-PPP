## Self-contained GUI

## Imports
# Kivy GUI
from kivy.config import Config
#Config.set('graphics','resizable',True)
#Config.set('graphics','fullscreen',1)
import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy.core.window import Window
Window.maximize()

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup

import time
import pandas as pd
import matplotlib
matplotlib.use('tkagg') # RaspPi specific backend
import matplotlib.pyplot as plt
import numpy as np

# Audio Recording
import threading
import datetime
import sounddevice as sd
from scipy.io import wavfile
from scipy.io.wavfile import write
import scipy.io
import wave, sys
#import vlc

#Plots test data when called
def plot_data():
    df = pd.read_csv('test_data.csv')
    df = df.drop('RawValue',axis=1)
    df = df.pivot(index='Frequency',columns='MeasNumber',values='BIOZ_MEAS')
    print(df)
    df.plot()
    plt.show()
 
def get_BIOZ():
    # Captures BIOZ data using arduino
    print('Getting BIOZ data')
 
def get_EGG():
    # Captures EGG data
    print('Getting BIOZ data')
 
class MenuScreen(Screen):
    def export_data(self):
        print("Export data to USB")
    
 
class VocalScreen(Screen):
    global fs
    fs = 48000
    global seconds
    seconds = 15 # 15 minute recording
    
    def start_recording(self):
       print("Starting recording of EGG and audio")
       global recording
       recording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
       global timestamp
       timestamp = str(datetime.datetime.today())
       timestamp = timestamp.replace(" ", "_").replace(":","-")
       print(timestamp)
       global record_timeout
       record_timeout = threading.Timer(seconds, self.stop_timer)
       record_timeout.start()
       #exec(open('get_EGG.py').read())
 
    def stop_recording(self):
       print("Stopping recording via button")
       sd.stop()
       #write(timestamp + ".wav", fs, recording)
       write("data/audio.wav", fs, recording)
       record_timeout.cancel()
 
    def stop_timer(self):
       print("Stopping recording via timer")
       sd.stop()
       #write(timestamp + ".wav", fs, recording)
       write("data/audio.wav", fs, recording)
       record_timeout.cancel()
 
    def plot_audio(self):
       #filepath = timestamp + ".wav"
       filepath = "data/audio.wav"
       sample_rate, audio_data = wavfile.read(filepath)
       length = audio_data.shape[0] / sample_rate
       time = np.linspace(0, length, audio_data.shape[0])
 
       plt.figure(1)
       plt.subplot(2, 1, 1)
       plt.plot(time,audio_data[:, 0], label="Left channel")
       plt.legend()
       plt.ylabel("Amplitude")
 
       plt.subplot(2, 1, 2)
       plt.plot(time,audio_data[:, 1], label="Right channel")
       plt.legend()
       plt.xlabel("Time [s]")
       plt.ylabel("Amplitude")
       plt.show()
 
    # Add function to handle BIOZ printing instead of separate
    # duplicate plot_test_data to here
    def plot_bioz_data(self):
        fig, (ax1, ax2) = plt.subplots(2,1)
        # Add resistance subplot
        filepath = "data/bioz.csv"
        df = pd.read_csv(filepath)     # Read csv file into DataFrame object
        #df = df.drop('ResistanceRaw',axis=1) # Drop RawValues column from object
        df = df.pivot(index='Frequency',columns='MeasNumber',values='ResistanceComputed')
            # Convert dataframe to pivot table
        print(df)   # Print pivot table to terminal to confirm values
        df.plot(ax=ax1, legend=None)   # Plot DataFrame object to matplotlib window
        #ax1.yaxis.set_label_text('Measured Resistance (Ohm)')
        #ax1.xaxis.set_label_text('Frequency (Hz)')
        #plt.axis([0, 128000, 0, 55])
        ax1.set_title('Measured Resistance (Ohm)')
        ax1.axis([0, 128000, 30, 55])
        
        # Add reactance subplot
        df = pd.read_csv(filepath)     # Read csv file into DataFrame object
        #df = df.drop('ReactanceRaw',axis=1) # Drop RawValues column from object
        df = df.pivot(index='Frequency',columns='MeasNumber',values='ReactanceComputed')
            # Convert dataframe to pivot table
        print(df)   # Print pivot table to terminal to confirm values
        df.plot(ax=ax2, legend=None)   # Plot DataFrame object to matplotlib window
        #ax2.yaxis.set_label_text('Measured Reactance (Ohm)')
        ax2.xaxis.set_label_text('Frequency (Hz)')
        ax2.set_title('Measured Reactance (Ohm)')
        ax2.axis([0, 128000, -10, 10])

        print("Displaying figures to user")
        fig.subplots_adjust(hspace=1.0)
        mng = plt.get_current_fig_manager()
        mng.resize(*mng.window.maxsize())
        plt.show()  # Show matplotlib figure
        print("User closed figure, exiting from BIOZ")

    def plot_egg_data(self):
        filepath = "data/egg.csv"
        df = pd.read_csv(filepath)
        #time_points = range(0, len(df.index)*100, 100)
        #df['time'] = time_points
        df.iloc[0:100].plot()
        plt.axis([0, 100, 0, 4500])
        plt.title('EGG capture (excerpt)')
        plt.xlabel("Sample index")
        plt.show()
    
    def open_audio(self):
        return
        player = vlc.MediaPlayer('data/audio.wav')
        player.play()
        player.audio_set_volume(50)
        time.sleep(15)

class MultipleScreens(App):
   pass

if __name__ == '__main__':
   MultipleScreens().run()
   