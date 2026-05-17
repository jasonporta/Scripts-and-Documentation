#!/usr/bin/python

# Print a slice from each line of a text file

import os
import sys
import glob
import itertools

starfile = './duplicates.csv'

for file in glob.glob(starfile):
   with open(file, 'r') as f:
      for line in itertools.islice(f, 403, None):
         for line in f:
            print(line[44:98])
