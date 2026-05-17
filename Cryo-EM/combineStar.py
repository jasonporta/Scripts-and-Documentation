#!/usr/bin/python

import sys
import glob
import itertools
import os
import subprocess

# Set goCTF output star files to files variable:
files = glob.glob('*.star')

# Combine individual star files generated from
# goCTF into one file called all_goCTF.star.

# Write the first star file to the output with header:
with open('all_goCTF.star','w+') as outfile:
  with open(files[0]) as f1:
    for line in f1:
      outfile.write(line)

# Write remaining star files to output minus the
# header and removing blank lines:
  for x in files[1:]:
    with open(x) as f1:
      for index,line in enumerate(f1):
        if index >= 23 and not line.isspace():
          outfile.write(line)
