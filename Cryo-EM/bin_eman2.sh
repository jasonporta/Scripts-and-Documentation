#!/bin/bash

mkdir binned_images

for file in ./*en-a.mrc
do
   e2proc2d.py $file binned_images/$file --meanshrink=4
done
