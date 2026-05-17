#!/usr/bin/bash
###Inherit all current environment variables
#PBS -V
### Job name
#PBS -N mrc2jpg
### Keep Output and Error
#PBS -k eo
### Queue name
#PBS -q batch
### Specify the number of nodes and thread (ppn) for your job.
#PBS -l nodes=1:ppn=1,pmem=12gb
### Tell PBS the anticipated run-time for your job, where walltime=HH:MM:SS
#PBS -l walltime=03:00:00
#################################
NSLOTS=$(wc -l $PBS_NODEFILE|awk {'print $1'})

### Switch to the working directory;
### Run:
module load eman2 relion
echo $INFILE
echo $OUTFILE
relion_image_handler --i $INFILE --o ${INFILE:r}_scale.mrc --angpix 1 --rescale_angpix 7.5 
e2proc2d.py ${INFILE:r}_scale.mrc $OUTFILE 
rm ${INFILE}_scale.mrc
