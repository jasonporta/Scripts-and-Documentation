#!/bin/bash

# make a new directory to store new images
mkdir phase_flipped

for file in ./*en.mrc
do
   relion_preprocess --phase_flip true --i $file --o phase_flipped/$file
done
