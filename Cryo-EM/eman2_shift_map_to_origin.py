#!/usr/local/bin/python3

# Load the default EMAN2 module
os.system('module load eman2')

# Import modules
import os
from EMAN2 import *

# Assign your map to the 'map' variable
map = EMData('input_map.mrc')

# Set the map position to zero for the x, y and z axes
map['origin_x']=0
map['origin_y']=0
map['origin_z']=0

# Write the newly shifted map
map.write_image(centered_map.mrc')


