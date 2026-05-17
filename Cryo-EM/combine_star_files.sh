#!/bin/bash

# Assign first file in the directory to variable 'first'###
first=$(ls -t *.star | head -1)

# Store header of the first file to variable 'header'###
header=$(cat $first | awk 'FNR<23 {print}')

for file in *.star
do
	cat $file | awk 'FNR>22 {print}' | sed '/^[[:space:]]*$/d'
done

#cat $header > particles.star
