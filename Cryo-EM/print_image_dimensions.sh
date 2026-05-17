#!/bin/sh

#Example run at command line interface: print_image_dimensions.sh > image_dimensions.txt

#Load EMAN2 module

module load eman2

#Print the image dimensions of images matching wildcard
#(i.e *.mrc, *.tif) and print stdout to a text file:

for file in *.tiff
do
	e2iminfo.py $file | sed '/40 total images/d'
done
