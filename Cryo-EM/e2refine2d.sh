#!/bin/bash

# All lines starting with "#PBS" are PBS commands 
# The following line asks for 10 nodes, each of which has 12 processors, for a total of 120 CPUs. 

#PBS -l nodes=10:ppn=12
#PBS -l walltime=48:00:00
#PBS -q batch
#PBS -V

#################################
echo Running on host `hostname`
echo Time is `date`
echo Working directory is `pwd`
#################################

NSLOTS=$(wc -l $PBS_NODEFILE|awk {'print $1'})
echo "Got $NSLOTS processors."
echo "I am running on" `hostname`
echo "My nodes are: "
cat $PBS_NODEFILE

echo "Changing to PBS_O_WORKDIR: $PBS_O_WORKDIR"
cd $PBS_O_WORKDIR

# Now the actual EMAN2 command(s). Note the --parallel option  at the end.
# The number of CPUs must match the number specified above. 

e2refine2d.py --input=sets/Final.lst --ncls=10 --iter=20 --nbasisfp=12 --automask --naliref=5 --center=xform.center --simalign=rotate_translate_tree --simaligncmp=ccc --simraligncmp=dot --simcmp=ccc --classkeep=0.85 --classiter=5 --classalign=rotate_translate_tree --classaligncmp=ccc --classraligncmp=ccc --classaverager=ctf.weight.autofilt --classcmp=ccc --classnormproc=normalize.edgemean --parallel=mpi:64:/lsi/tmp/jporta/
