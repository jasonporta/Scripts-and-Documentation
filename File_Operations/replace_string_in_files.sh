#!/bin/bash

# Define the directory to search in (e.g., current directory)
TARGET_DIR="./" 

# Define the string to find and the string to replace it with
OLD_STRING="/usr/bin/bash"
NEW_STRING="/bin/bash"

# Iterate through all files in the target directory
# The -type f ensures only regular files are processed (not directories)
# The -print0 and while read -r -d '' handle filenames with spaces or special characters
find "$TARGET_DIR" -type f -print0 | while IFS= read -r -d '' file; do
    # Use sed to perform the in-place replacement
    # -i ensures the change is made directly in the file
    # 's/OLD_STRING/NEW_STRING/g' performs a global substitution (all occurrences)
#   sed -i "s/$OLD_STRING/$NEW_STRING/g" "$file"
    sed "s/$OLD_STRING/$NEW_STRING/g" "$file"
    echo "Replaced '$OLD_STRING' with '$NEW_STRING' in: $file"
done
