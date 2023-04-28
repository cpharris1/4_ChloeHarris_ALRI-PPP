import pandas as pd
import matplotlib
matplotlib.use('tkagg') # RaspPi specific backend
import matplotlib.pyplot as plt
from adjustText import adjust_text

import numpy as np

filename = "max-50.csv"
folder = "test_data"
filepath = folder + "/" + filename

print("Creating figure from measurements")
#fig, (ax1, ax2) = plt.subplots(2,1)

freq = ['500', '1000', '2000', '4000', '8000', '18000', '40000', '80000', '128000']

# Add resistance subplot
df = pd.read_csv(filepath)     # Read csv file into DataFrame object
#print(df)


df1 = df.groupby('Frequency')[['ResistanceComputed', 'ReactanceComputed']].mean()
#df1.reset_index(inplace = True)



df1['ReactanceComputed'] = df1['ReactanceComputed'].abs()
print(df1)

low = df1.loc[500]
high = df1.loc[128000]


#Plot all 8 measurements
#df1.plot('ResistanceComputed', 'ReactanceComputed', legend=True, marker="o", ax=plt.gca())
plot = df1.plot('ResistanceComputed', 'ReactanceComputed', legend=None, marker="o")

# low_text = plt.text(low['ResistanceComputed'] - 2,low['ReactanceComputed']-0.05,"500 Hz")
# high_text = plt.text(high['ResistanceComputed'] +0.4 ,high['ReactanceComputed']-0.05,"128000 Hz")

#low_text = plt.text(low['ResistanceComputed']*0.95 ,low['ReactanceComputed']*0.99,"0.5 kHz")
#high_text = plt.text(high['ResistanceComputed']*1.02  ,high['ReactanceComputed']*0.99,"128 kHz")
low_text = plt.text(low['ResistanceComputed'] ,low['ReactanceComputed'],"0.5 kHz")
high_text = plt.text(high['ResistanceComputed'] ,high['ReactanceComputed'],"128 kHz")

objects = plot.get_lines()
#print(objects[0])

texts = [low_text, high_text]
adjust_text(texts, add_objects = objects, force_objects= (0.003, 0.1), only_move={'points':'xy', 'text':'xy', 'objects':'x'})

#print(df1['500'])

plt.xlabel('Resistance (Ohm)')
plt.ylabel('-Reactance (Ohm)')
plt.title('Bioimpedance')

#df = df.drop('ResistanceRaw',axis=1) # Drop RawValues column from object
#df = df.pivot(index='Frequency',columns='MeasNumber',values=['ResistanceComputed', 'ReactanceComputed'])
    # Convert dataframe to pivot table
#print(df)   # Print pivot table to terminal to confirm values
#df.plot('ResistanceComputed', 'ReactanceComputed')
plt.show() 
