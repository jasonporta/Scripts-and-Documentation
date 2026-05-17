#!/usr/bin/python

# Compress and remove files older than a defined time

import time,os,gzip

# Directory containing files to compress and/or delete
folder = "/path/to/files"

# Compress files older than given nuumber of days
compress_older_than = 5

# Delete files older than given number of days
delete_older_days = 90

# Current time
now = time.time()

# File cleaning function
def sanitize_files():
    # Loop through all the folder
    for file in os.listdir(folder): 
        f = os.path.join(folder,file)
        if not f.endswith('.gz'):
            if os.stat(f).st_mtime < now - (60*60*24*compress_older_than) and os.path.isfile(f):
                print ("...Compressing file "+f)
                out_filename = f + ".gz"
                
                f_in = open(f, 'rb')
                s = f_in.read()
                f_in.close()

                f_out = gzip.GzipFile(out_filename, 'wb')
                f_out.write(s)
                f_out.close()

                # Remove original uncompressed file
                os.remove(f)     
                
        # We ensure that the file we are going to delete has been compressed before
        if f.endswith('.gz'):
            if os.stat(f).st_mtime < now - (60*60*24*delete_older_days) and os.path.isfile(f):
                print ("...Deleting old file "+f)
                os.remove(f)
            
# Main program
if __name__ == '__main__':
    sanitize_files()
