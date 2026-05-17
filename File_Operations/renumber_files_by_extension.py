#!/usr/bin/python

import os

# Prompt the user for the directory path where the files need to be renamed
folder = input("Enter the path: ")

# Prompt the user to input the filetype
extension = input("Enter the file extension of the files to be renumbered: ")

# Get only the files needed and sort them
files = sorted(f for f in os.listdir(folder) if f.lower().endswith(extension))

for i, filename in enumerate(files, start=1):
    old_path = os.path.join(folder, filename)

    # Format number as 4 digits: 0001, 0002, ...
    number = f"{i:04d}"

    new_filename = f"img_{number}{extension}"
    new_path = os.path.join(folder, new_filename)

    os.rename(old_path, new_path)
