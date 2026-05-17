#!/bin/s

###################################################################### 
### What shell should your job run in
#PBS -S /bin/bash
### Job name
#PBS -N AutoPick
### Specify: Node, Processors Per Node, Memory Per Proc (nodes=1:ppn=6,pmem=12g)
#PBS -l nodes=1:ppn=6,pmem=12g
### Specify the maximum amount of time you want your job can run before being killed 
### (if omited defaults to 01:00:00 (1 day)
#PBS -l walltime=48:00:00
### Export all environment variables
#PBS -V
### Join stdout and stderr
#PBS -j oe
### Specify which queue to run the job on 
### - "batch" is the default queue (all nodes with <= 256GB memory)
### - "himem" consists of machines with >256GB memory (Currently just 1 machine)
### - "all.q" consists of all machines (please use sparingly).
#PBS -q batch
### If you want to receive an email on job abort/begin/end
#PBS -M jporta@umich.edu
#PBS -m abe
### Name file containing STDOUT
#PBS -o AutoPick.out
######################################################################


### Print some information regarding resource allocation.
#################################
echo Running on host `hostname`
echo Time is `date`
echo Working directory is `pwd`
#################################

NSLOTS = $(wc -l $PBS_NODEFILE | awk {'print $1'})
echo "There are $NSLOTS processors that have been allocated."
echo "I am running on" `hostname`
echo "My nodes are: "
cat $PBS_NODEFILE

echo "Changing to working directory: $PBS_O_WORKDIR"
cd $PBS_O_WORKDIR

### The mpirun command. Relion autopick option flags can be set 
### in the GUI if that is preferred.

/programs/x86_64-linux/system/openmpi/1.8.4/bin/mpirun --map-by slot -np $NSLOTS --machinefile $PBS_NODEFILE /programs/x86_64-linux/relion/2.1b1_cu8.0/bin/relion_autopick_mpi --i micrographs_ctf.star --ref Select/job062/class_averages.star --odir AutoPick/job064/ --pickname autopick --invert  --ctf  --ang 5 --shrink 1 --lowpass 20 --particle_diameter 198 --threshold 2.5 --min_distance 200 --max_stddev_noise 1.5 --only_do_unfinished --skip_optimise_scale
