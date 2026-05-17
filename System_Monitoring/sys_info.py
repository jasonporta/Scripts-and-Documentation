#!/usr/bin/python

import os
import shutil

def list_files(directory):
    print(f"Files in {directory}:")
    for file_name in os.listdir(directory):
        print(file_name)

def check_disk_usage():
    usage = shutil.disk_usage("/")
    print(f"Total: {usage.total // (1024**3)} GB")
    print(f"Used: {usage.used // (1024**3)} GB")
    print(f"Free: {usage.free // (1024**3)} GB")

def archive_logs(log_directory, archive_directory):
    if not os.path.exists(archive_directory):
        os.makedirs(archive_directory)
    for file_name in os.listdir(log_directory):
        if file_name.endswith(".log"):
            shutil.move(os.path.join(log_directory, file_name),
                        os.path.join(archive_directory, file_name))
            print(f"Archived: {file_name}")

# Main function calls
list_files("/var/log")
check_disk_usage()
archive_logs("/var/log", "/var/log/archived_logs")
