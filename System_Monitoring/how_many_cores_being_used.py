#!/usr/bin/python

import os 
import subprocess 

if os.path.exists('check_cluster.txt'): 
	os.remove('check_cluster.txt')

cmd='qstat -a | grep -v doozer | grep batch > check_cluster.txt'
subprocess.Popen(cmd,shell=True).wait()

numused=0
for line in open('check_cluster.txt','r'): 
	if line.split()[9] == 'R': 
		numused=float(line.split()[6])+numused

print '\nNumber of used cores = %0.f\n' %(numused)
