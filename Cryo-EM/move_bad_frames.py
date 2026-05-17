#!/usr/bin/python 

import os
import re
import shutil
import sys
import glob

path = 'bad_frames'
framesList = []
currentDir = os.getcwd()
total = len(glob.glob('*.tif'))

# Request user to input star file and check in current directory
star_file = input('\nEnter the name of your star file: ')
if not os.path.isfile(star_file):
   print('\nFile not found, now exiting...\n')
   sys.exit()

# Set permissions so only the owner is granted write access
permissions = 0o755

# Create directory to put the bad frames in
try:
   os.mkdir(path, permissions)
except OSError:
   print('\nCreation of directory %s has failed\n' % path)
else:
   print('\nDirectory %s has been created\n' % path)

# Open star file and make list of good frames
with open(star_file, 'r') as f:
   for file in f:
      match = re.findall(r'[\w-]+\.(?:mrc)', file)
      mod_match = (''.join(match))
      if not mod_match.strip(): continue
      frames = re.sub('(?<=en).*$','.frames.tif', mod_match)
      framesList.append(frames)
      good = len(framesList)

# Now grab the files not in framesList and move them to dir: bad_frames/
for file in glob.glob('*.tif'):
   if file not in framesList:
      shutil.move(file, path)
      print('Moving file %s to bad_frames/' % file)

bad = total - good
print('From a total of', total, 'TIF frames,', bad, 'bad frames were moved to bad_frames/')
