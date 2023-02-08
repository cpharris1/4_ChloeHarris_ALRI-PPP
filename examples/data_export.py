# Export data folder to external drive

#import os
#import shutil
import distutils
from distutils import dir_util

drivepath = "/media/pi/JALAYTON/data"

datapath = "data/"

# Copy all files in /data/ to /USB/data/
# Overwrite if necessary
#shutil.copytree(datapath, drivepath, dirs_exist_ok=True)
distutils.dir_util.copy_tree(datapath, drivepath)