#!/bin/bash

for file in *.tif
do
	e2iminfo.py -H $file | grep "images in\|total"
done
