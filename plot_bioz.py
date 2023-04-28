import pandas as pd
import matplotlib
matplotlib.use('tkagg') # RaspPi specific backend
import matplotlib.pyplot as plt

filename = "max-cole1.csv"
folder = "test_data"
filepath = folder + "/" + filename

print("Creating figure from measurements")
fig, (ax1, ax2) = plt.subplots(2,1)

# Add resistance subplot
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