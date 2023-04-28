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
from adjustText import adjust_text

import time
import datetime
import sounddevice as sd
from scipy.io import wavfile
from scipy.io.wavfile import write
import serial
import shutil

# importing mdapp from kivymd framework
from kivymd.app import MDApp
import threading

import os, sys

from kivy.config import Config

# Default to raspberry pi config, pass in argv w for windows testing
# For windows config execute as: python3 main.py w
pi = True
if((len(sys.argv)) > 1):
   if (sys.argv[1] == 'w'):
      pi = False

###############################   User Config   ##################################################
# The absolute path to the directory where app is being executed and where files are being stored. Must end in /
pi_dir = "/home/pi/4_ChloeHarris_ALRI-PPP/"

# The serial port of the Arduino. This may change based on the windows laptop or raspberry pi
win_port = "COM7"
pi_port = "/dev/ttyACM0"

# The number of seconds to record the audio data for
seconds = 5
##################################################################################################

# Window configuration. Raspberry pi touchscreen is 800x480. Want default background color to be white.
Window.clearcolor = (1, 1, 1, 1)
Window.size = (800, 480)

# Special config for windows to fix resolution bug
if not pi:
   from ctypes import windll, c_int64
   import win32api
   windll.user32.SetProcessDpiAwarenessContext(c_int64(-4))

# If on raspberry pi, full screen the app and disable the cursor for touchscreen
if(pi):
   Window.fullscreen = 'auto'
   Window.show_cursor = False

# Attempt to connect to the serial COM for the Arduino. A failed connection will only abort if on pi so
# that you can develop GUI on windows without physical connection
try:
   if(pi):
      port = pi_port
   else:
      port = win_port
   ser = serial.Serial(
      port,
      baudrate=115200,
      bytesize=serial.EIGHTBITS,
      parity=serial.PARITY_NONE,  # PARITY_EVEN & ODD have issues
      stopbits=serial.STOPBITS_ONE,
      timeout=1,
   )
   ser.reset_input_buffer()
except:
   # Exit the app if no serial connection on the pi.
   print("Error connecting to serial console.")
   if(pi):
      sys.exit()

# List of screen names that may be needed up update the patient ID on.
screenNames = ["BiozScreen1", "BiozScreen2", "AudioScreen1", "AudioScreen2", "ExportFileScreen"]

class HomeScreen(Screen):
   def update_id(self):
      """When the patient ID spinner is updated on home screen, update it on the other screens"""
      # Get the value of the spinner on the home screen
      home_ref = self.manager.get_screen("home_screen")
      pt_id = home_ref.ids.patient_id.text
      cl_id = home_ref.ids.clinician_id.text
      # Update the other screens in the screenNames list
      for name in screenNames:
         self.manager.get_screen(name).ids.patient_id.text = "Patient ID: "  + pt_id

class BiozScreen1(Screen):
   current_file = "bioz-test.csv"

   def update_spinner(self):
      """
      Update the spinners on the BiozScreen2 (the waiting screen) with the appropriate trial
      type and trial number
      """
      ref = self.manager.get_screen("BiozScreen2")
      ref.ids.trial_type.text = "Trial Type: " + self.ids.trial_type.text
      ref.ids.trial_num.text = "Trial Number: " + self.ids.trial_num.text

   def update_filename(self):
      """
      Dynamically generate and update the bioz filename using the spinners for patient id,
      trial type, trial number. Should follow the form "bioz-{pt_id}-{trial_type}{trial_num}.csv"
      """
      # Get the trial type and convert to an abbreviation (Br, Bd, E, A, M, or test)
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
      
      # Get the trial number, and the patient ID from the home screen
      trial_num = self.ids.trial_num.text
      pt_id = self.manager.get_screen("home_screen").ids.patient_id.text

      # Build the filename so that it shows all the information
      self.current_file = f"bioz-{pt_id}-{file_type}{trial_num}.csv"
      self.ids.fname.text = f"Filename: {self.current_file}"

   pass

class BiozScreen2(Screen):
   done = 0 # Flag used to determine whether the capture bioz is complete
   def get_filename(self):
      """
      Get the filename to display on the loading screen. After data is collected, it will be
      saved to this file.
      """
      fullstr = self.manager.get_screen("BiozScreen1").ids.fname.text
      return fullstr.split("Filename: ", 1)[1]

   def get_bioz(self):
      """
      Initiate the start of the measuring the bioz data. Sends the START cmd to the arduino COM port
      """
      self.done = False
      ser.reset_input_buffer()
      self.ser_writeread("START")
      self.ser_readBIOZ()
      return 1

   def ser_writeread(self, msg_out):
      """
      Helper function to write commands to the arduino COM port from the host
      """
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
      """ 
      Using readlines(), read until timeout triggers EOF
      NOTE: This could be buggy, if so swap to hardcoded stop
      Return the filestamp for later reading
      """
      while True:
         if ser.in_waiting > 0:
            msg_in = ser.readline().decode("utf-8").rstrip()
            print("< " + msg_in)
            if msg_in == "Measurements start":
                # End of print block, exit loop
                break
            
      # Get the filename we are writing the data to
      filename = self.get_filename()

      # Get the folder we are writing the data to. If on the pi, the folder should be in the
      # execution directory ./bioz but use the absolute path.
      folder = "bioz"
      if(pi):
         folder = pi_dir + folder

      # Generate the full filepath of the file, and open it for writing
      filepath = folder + "/" + filename
      fileHandler = open(filepath, "w")

      #Copy the measurements into the file
      while True:
         if ser.in_waiting > 0:
               msg_in = ser.readline().decode("utf-8").rstrip()
               #print("< " + msg_in)
               if msg_in == "Measurements done":
                  # End of print block, exit loop
                  break
               else:
                  # Valid data, print to file
                  fileHandler.write(msg_in + "\n")

      # Close the file and return the filepath
      fileHandler.close()
      return filepath

   def start_background_task_bioz(self):
      """ 
      Entry point to start collecting bioz data in the background so the loading screen
      animation works. Counts down from 3 then generates a new thread to call the get_bioz function from.
      """
      # Reset done flag and configure screen to show it is collecting data
      self.ids.spinner.active = False

      # Callback function used to count down 3, 2, 1, then start data collection in new thread.
      def count_it(num):
        if(num == 0):
           # Start the spinner animation and start collecting data
           self.ids.spinner.active = True
           self.ids.status.text = "Collecting BioZ Data..."
           # Start the new thread to get the bioz data from the arduino COM
           thread = threading.Thread(target = self.background_get_bioz)
           thread.start()
           return
        # Update the number displayed on screen
        self.ids.status.text = str(num)
        num -= 1
        # Wait for a second, then display next number
        Clock.schedule_once(lambda dt: count_it(num), 1)

      # Start the countdown timer, then start collecting data
      Clock.schedule_once(lambda dt: count_it(3), 0)

   def background_get_bioz(self, *args):
      """ 
      Starts the process that collects bioz data in a separate thread
      """
      self.done = False
      result =0
      # If we are using windows development mode, just sleep and don't actually call the function
      # since it is not guaranteed the COM port is open. If on the pi, actually collect data.
      if not pi:
         sleep(5)
         result = 1
      else:
         result = self.get_bioz()
      
      # Once the get bioz function is done, set the flag that we are now done, and update the GUI
      if (result != None):
         self.done = True
         self.update()

   @mainthread
   def update(self):
      """
      Updates the GUI and the main thread once we have collected all the data. Move directly to the
      show bioz screen so we can view the data immediately.
      """
      if(self.done):
         self.ids.spinner.active = False
         self.ids.status.text = "Done!"
         self.manager.get_screen("ViewBiozScreen1").plot_bioz_zvr()

   pass

class BiozHelp(Screen):
   pass

class ExportFileScreen(Screen):
   drive_name = "none"
   drive_path = "none"
   def update_preview(self):
      """
      Show a preview of the contents of the selected drive. Currently not being used...
      """
      #self.drive_name = self.ids.usb_drive.text
      if(self.drive_name == "none"):
         self.ids.dir_preview.text = "No drive selected."
      else:
         files = ["None"]
         try:
            files = os.listdir(self.drive_path)
            files = [x for x in files if not x.startswith('.')]
         except:
            print("Error reading drive")
         file_str = "\n".join(str(x) for x in files[:5])
         full_str = "Drive Preview:\n" + file_str
         self.ids.dir_preview.text = full_str

   def search_drives(self):
      """
      Look for new USB drives plugged in and update the list of available drives to
      choose from. Drives should be mounted in /media/pi/ folder on the pi.
      """
      # Do not show that the files have copied over yet.
      available_drives = []
      self.ids.check_done.opacity = 0
      self.ids.text_done.opacity = 0
      self.ids.text_done.text = "Files have not copied yet."

      # Depending on the OS, find the list of available drives and add it to a list
      if(not pi):
         win_drives = win32api.GetLogicalDriveStrings()
         available_drives = win_drives.split('\000')[:-1]
         # Ignore the C drive since we want just the usb drives
         if("C:\\"in available_drives):
            available_drives.remove("C:\\")
      else:
         available_drives = os.listdir('/media/pi/')
         # ALRI-pi has a JALAYTON folder in the media drive. Ignore.
         if("JALAYTON" in available_drives):
            available_drives.remove("JALAYTON")

      # Update the dropdown with the list of available drives
      self.ids.usb_drive.values = available_drives
      if(available_drives):
         # auto select the first drive if one is avaliable.
         self.ids.usb_drive.text = available_drives[0]
      else:
         # If no drives were found, reset values
         self.ids.usb_drive.text = "No Drives Found"
         self.drive_name = "none"
         self.drive_path = "none"

   def update_selected(self):
      """
      Updates internal attributes for drive path and drive name used in other methods.
      """
      # Grab the drive that is selected by the dropdown menu
      drive = self.ids.usb_drive.text
      # Set the name and drive path based on the OS
      if(drive != "No Drives Found"):
         if(pi):
            self.drive_path = '/media/pi/' + drive
         else:
            self.drive_path = drive
         self.drive_name = drive
      else:
         self.drive_name = "none"
         self.drive_path = "none"
   
   def export(self):
      """
      Copies the data files in the ./audio and ./bioz folder to the drive selected.
      Note, if a file already exists on the drive, it will be overwritten.
      """
      # Reset flags and GUI control for "done" message
      error = False
      self.ids.check_done.opacity = 0
      self.ids.text_done.opacity = 0

      # Get the absolute path for where the audio and bioz data is stored.
      audio_source = os.path.abspath("audio")
      bioz_source = os.path.abspath("bioz")
      sources = [audio_source, bioz_source]

      # Get the path of the USB drive (the destination folder)
      destination_dir = self.drive_path
      
      # If there is a valid destination, attempt copy
      if(destination_dir != "none"):
         try:
            # Loop through each folder /audio and /bioz
            for source_dir in sources:
               # for each file in the data folder
               for file_name in os.listdir(source_dir):
                  # construct the full source and destination file path (appropriate to OS)
                  slash = "/" if pi else "\\"
                  source = source_dir + slash + file_name
                  destination = destination_dir + slash + file_name
                  # Only copy the files
                  if os.path.isfile(source):
                     shutil.copy(source, destination)
         except:
            # An error has occured. Notify the user.
            print("Error copying files.")
            self.ids.text_done.opacity = 1
            self.ids.text_done.text = "Error copying files."
            error = True
         if (not error):
            # Files were successfully copied, show the success message and checkmark
            print("Files successfully copied to drive: " + destination_dir)
            self.ids.check_done.opacity = 1
            self.ids.text_done.opacity = 1
            self.ids.text_done.text = "Files successfully copied to drive: " + destination_dir
      else:
         # We cannot copy if there is no drive selected. Notify the user.
         self.ids.text_done.opacity = 1
         self.ids.text_done.text = "No USB drive selected. Please select drive or press refresh."
   pass

class ViewBiozScreen1(Screen):
   done = False
   def get_filename(self):
      """
      Get the correct filename from the biozscreen1 to display
      """
      fullstr = self.manager.get_screen("BiozScreen1").ids.fname.text
      return fullstr.split("Filename: ", 1)[1]

   def plot_bioz(self):
      """
      Plot the bioz data as two separate subplots of reactance and resistance vs frequency with 
      each with 8 lines for the 8 different measurements. Currently not used, but kept in case
      you want to change. Change instances of plot_bioz_zvr() to plot_bioz()
      """
      # Clear the previous graph
      self.ids.bioz_graph.clear_widgets()

      # Get the file name
      filename = self.get_filename()
      folder = "bioz"
      if(pi):
         folder = pi_dir + "bioz"
      # build the file path
      savedFile = folder + "/" + filename

      # Error check to see if the file exists, otherwise display dummy data (used for testing/debug)
      if not (os.path.isfile(savedFile)):
         filename = "test-bioz.csv"
         print("Error: File not found.")
         savedFile = folder + "/test-bioz.csv"

      # Update GUI to display filename
      self.ids.fname.text = f"Displaying data from: {filename}"

      # Clear the current figure
      plt.clf()

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

      #print("Displaying figures to user")
      fig.subplots_adjust(hspace=1.0)
      # Actually generate and embed the plot in the GUI
      self.ids.bioz_graph.add_widget(FigureCanvasKivyAgg(plt.gcf()))
      self.manager.current = "ViewBiozScreen1"
      return 1
   
   def plot_bioz_zvr(self):
      """
      Plot the bioz data from a given file. Creates plot of -reactance vs resistance.
      """
      # Clear the plot in the GUI
      self.ids.bioz_graph.clear_widgets()

      # Get the filename of the data we want to plot and build the filepath
      filename = self.get_filename()
      folder = "bioz"
      if(pi):
         folder = pi_dir + "bioz"
      savedFile = folder + "/" + filename

      # If the file is invalid, print the dummy data (to be used for testing/debug)
      if not (os.path.isfile(savedFile)):
         filename = "test-bioz.csv"
         print("Error: File not found.")
         savedFile = folder + "/test-bioz.csv"

      # Update the GUI so the user knows what file is being displayed
      self.ids.fname.text = f"Displaying data from: {filename}"

      # Clear the plot
      plt.clf()
      # Read csv file into DataFrame object
      df = pd.read_csv(savedFile)     

      # Group the data by frequency, and find the mean of the reactance and resistance for each frequency
      df1 = df.groupby('Frequency')[['ResistanceComputed', 'ReactanceComputed']].mean()

      # Get the value of the reactance (reactance values should be negative, but we want -reactance)
      df1['ReactanceComputed'] = df1['ReactanceComputed'].abs()
      print(df1)

      # Get the coordinates of the low frequency and high frequency (500Hz and 128kHz) for labelling purposes
      low = df1.loc[500]
      high = df1.loc[128000]

      #Plot all 8 measurements
      #df1.plot('ResistanceComputed', 'ReactanceComputed', legend=True, marker="o", ax=plt.gca())

      # Plot the data
      plot = df1.plot('ResistanceComputed', 'ReactanceComputed', legend=None, marker="o")
      # Label the high and low frequency points
      low_text = plt.text(low['ResistanceComputed'] ,low['ReactanceComputed'],"0.5 kHz")
      high_text = plt.text(high['ResistanceComputed'] ,high['ReactanceComputed'],"128 kHz")

      # Get the line objects (used for adjust_text)
      objects = plot.get_lines()
      # Use the adjust_text library to repel labels from the graph and other data points (may not always work...)
      texts = [low_text, high_text]
      adjust_text(texts, add_objects = objects, force_objects= (0.004, 0.01), only_move={'points':'xy', 'text':'xy', 'objects':'x'})
      # Add axis labels
      plt.xlabel('Resistance (Ohm)')
      plt.ylabel('-Reactance (Ohm)')
      # Actually generate and embed the plot in the GUI
      self.ids.bioz_graph.add_widget(FigureCanvasKivyAgg(plt.gcf()))
      self.manager.current = "ViewBiozScreen1"

   def update_new_filename(self):
      """
      Update the filenames to show the correct new file (when user selects to automatically go to next trial)
      """
      ref = self.manager.get_screen("BiozScreen1")

       # Get the trial type and convert to an abbreviation (Br, Bd, E, A, M, or test)
      trial_type = ref.ids.trial_type.text
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
      
      # Get the trial number of the new current trial
      trial_num = str((int)(ref.ids.trial_num.text))
      # Get the patient id from the home screen
      pt_id = ref.manager.get_screen("home_screen").ids.patient_id.text
      # Update the current file to be the new incremented file
      ref.current_file = f"bioz-{pt_id}-{file_type}{trial_num}.csv"
      ref.ids.fname.text = f"Filename: {ref.current_file}"

      # Update the next filename on the plot screen to show the next trial
      next_num = str((int)(ref.ids.trial_num.text)+1)
      next_f = f"bioz-{pt_id}-{file_type}{next_num}.csv"
      self.ids.fname_next.text = f"    Next filename: {next_f}"

   def next_file(self):
      """
      User wants to automatically start the next trial. Update filenames on all screens accordingly.
      """
      if("test" not in self.ids.fname.text):
         # Get the reference to the BiozScreen1
         ref = self.manager.get_screen("BiozScreen1")
         # Determine the trial number of the next trial
         next_trial = str((int)(ref.ids.trial_num.text) + 1)
         # Update the dropdown menus to show the next trial
         ref.ids.trial_num.text = next_trial
         ref.ids.trial_num.value = next_trial
         # Update the filenames to show the next trial number
         ref.update_filename()
         self.update_new_filename()

   pass

class AudioScreen1(Screen):
   current_file = "test.wav"
   def update_filename(self):
      """
      Update the filename of the audio file if the patient id changes
      """
      pt_id = self.manager.get_screen("home_screen").ids.patient_id.text

      self.current_file = f"audio-{pt_id}.wav"
      self.ids.fname.text = f"Filename: {self.current_file}"
   pass

class AudioScreen2(Screen):
   done = False

   def get_filename(self):
      """
      Get the filename of the audio file on the audioscreen1
      """
      fullstr = self.manager.get_screen("AudioScreen1").ids.fname.text
      return fullstr.split("Filename: ", 1)[1]
   
   def get_audio(self):
      """
      Record the fixed length audio sample and save it as a .wav file
      """
      # Set the sampling frequency
      fs = 48000
      print("Start recording")
      # Record for fixed number of seconds
      recording = sd.rec(int(seconds*fs), samplerate=fs, channels=2)
      sd.wait()

      # Get the filename to save data to and build the filepath
      filename = self.get_filename()
      folder = "audio"
      if(pi):
         folder = pi_dir + "audio"
      filepath = folder + "/" + filename

      # Write the audio data to the .wav file
      print("Stop recording, save to file")
      write(filepath, fs, recording)
      return 1

   def start_background_task_audio(self):
      """ 
      Entry point to start collecting audio data in the background so the loading screen
      animation works. Counts down from 3 then generates a new thread to call the get_audio function from.
      """
      # Reset done flag and configure screen to start countdown
      self.ids.spinner.active = False
      self.done = False

      # Callback function used to count down 3, 2, 1, then start data collection in new thread.
      def count_it(num):
        if(num == 0):
           # Start the spinner animation and start collecting data
           self.ids.spinner.active = True
           self.ids.status.text = "Recording Audio..."
           # Start the new thread to get the bioz data from the arduino COM
           thread = threading.Thread(target = self.background_get_audio)
           thread.start()
           return
        # Update the number displayed on screen
        self.ids.status.text = str(num)
        num -= 1
        # Wait for a second, then display next number
        Clock.schedule_once(lambda dt: count_it(num), 1)

      # Start the countdown timer, then start collecting data
      Clock.schedule_once(lambda dt: count_it(3), 0)

   def background_get_audio(self, *args):
      """
      Function called to record audio data in new thread so GUI animations don't get blocked
      """
      result = self.get_audio()
      # Once the recording is finished, update the GUI and move on to the show audio screen
      if (result != None):
         self.done = True
         self.update()

   @mainthread
   def update(self):
      """
      Mainthread function to update the GUI and move on to show the audio data
      """
      if(self.done):
         self.ids.spinner.active = False
         self.ids.status.text = "Done!"
         self.manager.get_screen("ViewAudioScreen1").plot_audio()
   pass

class ViewAudioScreen1(Screen):
   def get_filename(self):
      """
      Get the filename from the audioscreen1 (file we are displaying data for)
      """
      fullstr = self.manager.get_screen("AudioScreen1").ids.fname.text
      return fullstr.split("Filename: ", 1)[1]
   
   def plot_audio(self):
      """
      Function to plot the FFT of the audio data of a given filename
      """
      # Clear the plot
      self.ids.audio_graph.clear_widgets()
      # Get the filename of the data and build the filepath
      filename = self.get_filename()
      folder = "audio"
      if(pi):
         folder = pi_dir + "audio"
      savedFile = folder + "/" + filename
      # If it is not a valid file, show the dummy data (for testing purposes)
      if not (os.path.isfile(savedFile)):
         filename = "test-audio.wav"
         savedFile = folder + "/test-audio.wav"
         print("Oops, file not found")
      # Update the GUI so the user knows which file's data is being displayed
      self.ids.fname.text = f"Displaying data from: {filename}"
      # Clear the plot
      plt.clf()

      # Generate arrays for the FFT
      sample_rate, audio_data = wavfile.read(savedFile)
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

      # Plot the FFT
      plt.plot(freq, fft_spectrum_abs)
      # Label axis
      plt.xlabel("frequency, Hz")
      plt.ylabel("Amplitude, units")
      # Actually update the GUI with the plot
      self.ids.audio_graph.add_widget(FigureCanvasKivyAgg(plt.gcf()))
      self.manager.current = "ViewAudioScreen1"
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