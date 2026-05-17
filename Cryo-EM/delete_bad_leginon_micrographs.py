#!/usr/bin/python

import os
import sys
import glob
import re

logFile = './hidden.log'
searchLog = 'be deleted'
hiddenImages = []
framesList = []

framesPath = raw_input('\nEnter the path where your frames are located: ')

###Check if frames directory exists###
if not os.path.exists(framesPath):
  print '\nDirectory does not exist, now exiting...\n'
  sys.exit()

###Set working directory to user input###
def workDir(framesPath):
  os.chdir(framesPath)

###Search for files to delete and add them to a list###
for file in glob.glob(logFile):
  with open(file,'r') as f:
    tempList = []
    for line in f:
      if searchLog in line:
        tempList.append(line.split()[1])
    hiddenImages.append(tempList)
###Change the name of the 'en' files to 'frames' and delete them###
for line in hiddenImages[-1]:
  workDir(framesPath)
  match = re.findall('\S*en\s*',line)
  if match:
    framesList.append(match[0] + '.frames.tif')
    print framesList
    if os.path.isfile(framesList[-1]):
      print framesList[-1]
#     os.remove(framesList[-1])
      
print '\nDeleted ',len(framesList),' frames in ' + os.getcwd() + '\n'
