#!/bin/bash

#Make list of micrographs that exceed
#a user-defined maximum resolution.

#Print all micrographs from ctfdata.dat
#with their corresponding res(pkg):

awk '{print $10,$15}' ctfdata.dat > images.txt

#Make a new list with micrographs below
#a user-defined resolution:

awk '($1 > 5)' images.txt > imagesReso.txt

#Print list of micrographs filtered out:

awk 'FNR > 1 {print $2}' imagesReso.txt > imagesDel.txt

#Remove these files from micrographs_gctf.star:

grep -wvf imagesDel.txt micrographs_gctf.star > micrographs_gctf-final.star

#Append .mrc to the end of each line:

sed -e 's/$/.mrc/' -i imagesDel.txt

#Delete these images from directory:

xargs -a imagesDel.txt -d'\n' rm

#Clean-up files:

rm images.txt imagesReso.txt imagesDel.txt
