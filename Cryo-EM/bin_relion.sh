#!/bin/bash

# make a new directory to store binned images
mkdir binned_images

# run the relion_image_handler executable for every image in
# the directory ending with *en-a.mrc, bin the data 4-fold and 
# save the binned images to the binned_images directory
for file in ./*en-a.mrc
do
   relion_image_handler --rescale_angpix 4.0 --i $file --o binned_images/$file
done
