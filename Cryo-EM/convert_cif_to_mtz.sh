#!/bin/bash

# Load CCP4i module
#module load ccp4

# Read the user's input CIF file
read -p "Please enter the input CIF file: " file1
echo "The file you input is named: $file1"

sleep 5s

# Read the user's output file
read -p "Please enter a name for the output MTZ: " file2
echo "Your outfile is named: " $file2

# Convert CIF to MTZ format
cif2mtz $file1 $file2 <<EOF
EOF
