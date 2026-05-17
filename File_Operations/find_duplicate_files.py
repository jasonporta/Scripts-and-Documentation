#!/usr/bin/python3

import os
import hashlib
from collections import defaultdict

def hash_file(filepath, blocksize=65536):
    """Generates the SHA1 hash of a file."""
    hasher = hashlib.sha1()
    with open(filepath, 'rb') as f:
        buf = f.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(blocksize)
    return hasher.hexdigest()

def find_duplicate_files(directory):
    """
    Finds duplicate files in a given directory and its subdirectories.
    Returns a dictionary where keys are file hashes and values are lists of file paths.
    """
    files_by_size = defaultdict(list)
    files_by_hash = defaultdict(list)
    duplicate_files = []

    # First pass: Group files by size
    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                file_size = os.path.getsize(filepath)
                files_by_size[file_size].append(filepath)
            except OSError:
                continue  # Skip inaccessible files

    # Second pass: Hash files that have the same size
    for size, file_list in files_by_size.items():
        if len(file_list) > 1:  # Only check if there are multiple files of the same size
            for filepath in file_list:
                file_hash = hash_file(filepath)
                files_by_hash[file_hash].append(filepath)

    # Identify duplicates based on hash
    for file_hash, file_list in files_by_hash.items():
        if len(file_list) > 1:
            duplicate_files.append(file_list)

    return duplicate_files

if __name__ == "__main__":
    target_directory = input("Enter the directory to scan for duplicates: ")

    if not os.path.isdir(target_directory):
        print(f"Error: '{target_directory}' is not a valid directory.")
    else:
        duplicates = find_duplicate_files(target_directory)

        if duplicates:
            print("\nDuplicate files found:")
            for group in duplicates:
                print("---")
                for filepath in group:
                    print(filepath)
        else:
            print("No duplicate files found.")
