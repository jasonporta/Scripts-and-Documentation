#!/bin/bash

i = 3872145

if [i -le 3872344]
then
	qdel i
	i++
else
	exit 1
fi
