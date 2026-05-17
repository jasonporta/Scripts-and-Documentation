#!/usr/bin/bash

# Remove all symbolically linked files in the current directory
for name in $(find . -type l); do
	unlink $name
	echo "Unlinking $name"
done
