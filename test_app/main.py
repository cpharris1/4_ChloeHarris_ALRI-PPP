from kivy.app import App
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition, FadeTransition
from kivy.core.window import Window
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.clock import Clock, mainthread
from kivymd.icon_definitions import md_icons
from time import sleep

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

from kivy.garden.matplotlib import FigureCanvasKivyAgg

# from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

import time
import datetime
import sounddevice as sd
from scipy.io import wavfile
from scipy.io.wavfile import write
import serial

# importing mdapp from kivymd framework
from kivymd.app import MDApp
import threading

import os

from ctypes import windll, c_int64
from kivy.config import Config


pi = False

if not pi:
   windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))

Window.clearcolor = (1, 1, 1, 1)
Window.size = (800, 480)
if(pi):
   Window.fullscreen = 'auto'
   Window.show_cursor = False


# Config.set("graphics", "show_cursor", 1)
# Config.write()


try:
   port = "COM7"
   if(pi):
      port = "/dev/ttyACM0"
   ser = serial.Serial(
      #"/dev/serial0", # RPi port
      port, # Windows port
      baudrate=115200,
      bytesize=serial.EIGHTBITS,
      parity=serial.PARITY_NONE,  # PARITY_EVEN & ODD have issues
      stopbits=serial.STOPBITS_ONE,
      timeout=1,
   )
   ser.reset_input_buffer()
except:
   print("Error connecting to serial console.")




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

screenNames = ["BiozScreen1", "BiozScreen2", "AudioScreen1", "AudioScreen2"]

class HomeScreen(Screen):
   def update_id(self):
      # TODO: You may not need this fxn anymore
      #print("")
      home_ref = self.manager.get_screen("home_screen")
      pt_id = home_ref.ids.patient_id.text
      cl_id = home_ref.ids.clinician_id.text
      for name in screenNames:
         self.manager.get_screen(name).ids.patient_id.text = "Patient ID: "  + pt_id
      #    self.manager.get_screen(name).ids.clinician_id.text = cl_id

class BiozScreen1(Screen):
   current_file = "bioz-test.csv"
   def update_spinner(self):
      ref = self.manager.get_screen("BiozScreen2")
      ref.ids.trial_type.text = "Trial Type: " + self.ids.trial_type.text
      ref.ids.trial_num.text = "Trial Number: " + self.ids.trial_num.text

   def update_filename(self):
      trial_type = self.ids.trial_type.text
      file_type = 'test'
      if(trial_type == 'Breathing'):
         file_type = "Br"
      elif(trial_type == 'Bearing Down'):
         file_type = "Bd"
      elif(trial_type == 'Eeee'):
         file_type = "E"
      elif(trial_type == 'Aaahhh'):
         file_type = "A"
      elif(trial_type == 'Moving'):
         file_type = "M"
      
      trial_num = self.ids.trial_num.text
      pt_id = self.manager.get_screen("home_screen").ids.patient_id.text

      self.current_file = f"bioz-{pt_id}-{file_type}{trial_num}.csv"
      self.ids.fname.text = f"Filename: {self.current_file}"



   pass

class BiozScreen2(Screen):
   done = 0
   #fname = 'test-bioz.csv'
   def get_filename(self):
      fullstr = self.manager.get_screen("BiozScreen1").ids.fname.text
      return fullstr.split("Filename: ", 1)[1]

   def get_bioz(self):
      self.done = False
      ser.reset_input_buffer()
      self.ser_writeread("START")
      self.ser_readBIOZ()
      return 1

   def ser_writeread(self, msg_out):
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
   def ser_readBIOZ(self):
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
      filename = self.get_filename()
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

   def start_background_task(self):
      self.done = False
      self.ids.status.text = "Collecting BioZ Data..."
      self.ids.saved.opacity = 0
      thread = threading.Thread(target = self.callFunction)
      thread.start()
      #thread.join()
      #self.manager.current = 'home_screen'

   def callFunction(self, *args):
      result =0
      if not pi:
         sleep(5)  #TODO: uncomment and remove and reinit the get_bioz
         result = 1
      else:
         result = self.get_bioz()
      #if result != None:
      #   self.manager.current = 'home_screen'
      if (result != None):
         self.done = True
         self.update()

   @mainthread
   def update(self):
      if(self.done):
         self.ids.spinner.active = False
         self.ids.status.text = "Done!"
         self.ids.saved.text = f"Saved data to file: {self.get_filename()}"
         self.ids.saved.opacity = 1
         self.manager.get_screen("ViewBiozScreen1").plot_bioz()
   pass

class BiozHelp(Screen):
   pass

class ViewBiozScreen1(Screen):
   done = False
   def get_filename(self):
      fullstr = self.manager.get_screen("BiozScreen1").ids.fname.text
      return fullstr.split("Filename: ", 1)[1]

   def plot_bioz(self):
      self.ids.bioz_graph.clear_widgets()

      filename = self.get_filename()
      folder = "bioz"
      savedFile = folder + "/" + filename
      if not (os.path.isfile(savedFile)):
         filename = "test-bioz.csv"
      savedFile = folder + "/test-bioz.csv"

      self.ids.fname.text = f"Displaying data from: {filename}"

      #print("Creating figure from measurements")
      fig, (ax1, ax2) = plt.subplots(2,1)

      # Add resistance subplot
      df = pd.read_csv(savedFile)     # Read csv file into DataFrame object
      #df = df.drop('ResistanceRaw',axis=1) # Drop RawValues column from object
      df = df.pivot_table(index='Frequency',
                           columns='MeasNumber',
                           values='ResistanceComputed',
                           aggfunc='mean')
         # Convert dataframe to pivot table
      #print(df)   # Print pivot table to terminal to confirm values
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
      #print(df)   # Print pivot table to terminal to confirm values
      df.plot(ax=ax2, legend=None, logx=True)   # Plot DataFrame object to matplotlib window
      ax2.xaxis.set_label_text('Frequency (Hz)')
      ax2.set_title('Measured Reactance (Ohm)')
      #ax2.axis([0, 128000, -5, 5])

      #print("Displaying figures to user")
      fig.subplots_adjust(hspace=1.0)
      #mng = plt.get_current_fig_manager()
      #mng.resize(*mng.window.maxsize())
      #mng.window.state('zoomed')
      #plt.show()  # Show matplotlib figure
      #print("User closed figure, exiting from BIOZ")
      self.ids.bioz_graph.add_widget(FigureCanvasKivyAgg(plt.gcf()))
      self.manager.current = "ViewBiozScreen1"
      return 1

   pass

class AudioScreen1(Screen):
   current_file = "test.wav"
   def update_filename(self):
      pt_id = self.manager.get_screen("home_screen").ids.patient_id.text

      self.current_file = f"audio-{pt_id}.wav"
      self.ids.fname.text = f"Filename: {self.current_file}"
   pass

class AudioScreen2(Screen):
   done = False

   def get_filename(self):
      fullstr = self.manager.get_screen("AudioScreen1").ids.fname.text
      return fullstr.split("Filename: ", 1)[1]
   
   def get_audio(self):
      fs = 48000
      seconds = 5
      print("Start recording")
      recording = sd.rec(int(seconds*fs), samplerate=fs, channels=2)
      sd.wait()
      filename = self.get_filename()
      folder = "audio"
      filepath = folder + "/" + filename
      print("Stop recording, save to file")
      write(filepath, fs, recording)
      return 1

   def start_background_task(self):
      self.done = False
      self.ids.status.text = "Recording Audio..."
      self.ids.saved.opacity = 0
      thread = threading.Thread(target = self.callFunction)
      thread.start()
      #thread.join()
      #self.manager.current = 'home_screen'

   def callFunction(self, *args):
      result = self.get_audio()
      if (result != None):
         self.done = True
         self.update()

   @mainthread
   def update(self):
      if(self.done):
         self.ids.spinner.active = False
         self.ids.status.text = "Done!"
         self.ids.saved.text = f"Saved data to file: {self.get_filename()}"
         self.ids.saved.opacity = 1
         #self.manager.get_screen("ViewBiozScreen1").plot_bioz()
   pass

class ViewAudioScreen1(Screen):
   pass

class EGGScreen1(Screen):
   pass

class ViewEGGScreen1(Screen):
   pass


class RootWidget(ScreenManager):
   pass


class MainApp(MDApp):

   def build(self):
      self.title = "ALRI App"

      return RootWidget(transition=NoTransition())
      

if __name__ == "__main__":
    MainApp().run()