#!/usr/bin/python

# Invoke this script with an input directory to compres all TIF
# frame stacks into MRC files, then remove the .tif files.

import time 
import sys
import glob
import os
import subprocess

def query_yes_no(question, default="yes"):
    """Ask a yes or no question from the user's input and return their answer.
    Hitting <Enter> without input will default to "yes".
    The return value is either "yes" or "no".
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please use either 'yes' or 'no' "\
                    "(or 'y' or 'n').\n")

if len(sys.argv) != 2:
    print("\nTake an input directory and compress all TIFF into MRC and remove the TIFs \n")
    print("\nTo use: ./batch_convert_tif2mrc.py [full path to directory name]\n")
    sys.exit()

indirectory=sys.argv[1]

# Check if the input directory exists
if not os.path.exists(indirectory):
    print(('Error: Input directory does not exist %s' %(indirectory)))
    sys.exit()

# Determine the number of TIF and MRC files
numTIFF=len(glob.glob('%s/*.tif' %(indirectory)))
numMRC=len(glob.glob('%s/*.mrc' %(indirectory)))

if numMRC > 0: 
    ans=query_yes_no("\nThere are  %i .tif and %i .mrc files in the input directory %s \n\nDo you wish to continue?" %(numTIFF,numMRC,indirectory))
    if ans is False:
        sys.exit()

ans=query_yes_no("\nFound %i movies with .tif extension %s\n\nDo you want to convert .tif to .mrc files?" %(numTIFF,indirectory))

if ans is True:
    print("\nConverting files and submitting to the cluster...")
    delans=query_yes_no("\nDo you wish to delete the TIF files after compression?\n")
    counter=1
    for tif in glob.glob('%s/*.tif' %(indirectory)):
        tifsplit=tif.split('.')
        del tifsplit[-1]
        outname='%s.mrc' %('.'.join(tifsplit))
        if not os.path.exists(outname):
            cmd='tif2mrc %s %s' %(tif,outname)
            if delans is True: 
                cmd=cmd+'\n'+'rm %s' %(tif)
                outfile='submit_%i.sh' %(int(time.time()))
                o1=open(outfile,'w')
                o1.write('#!/bin/bash\n')
                o1.write('#PBS -V\n')
                o1.write('#PBS -N tif2mrc\n')
                o1.write('#PBS -k eo\n')
                o1.write('#PBS -q batch\n')
                o1.write('#PBS -l nodes=1:ppn=1\n')
                o1.write('#PBS -l walltime=0:60:00\n')
                o1.write('NSLOTS=$(wc -l $PBS_NODEFILE|awk {"print $1"})\n')
                o1.write('source /Users/jporta/modules.sh\n')
                o1.write('module load imod\n')
                o1.write('cd $PBS_O_WORKDIR\n')
                o1.write('%s\n' %(cmd))
                o1.close()

                cmd='qsub %s' %(outfile)
                subprocess.Popen(cmd,shell=True).wait()

                if counter%100 == 0:
                    print(('%i movies submitted...' %(counter)))
                    time.sleep(400)

            os.remove(outfile)
            counter=counter+1

    print(("\n%i movies submitted to the cluster for compression using tif2mrc" %(counter-1)))
