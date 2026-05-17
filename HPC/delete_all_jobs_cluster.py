#!/usr/bin/env python

import subprocess
import os 

if os.path.exists('jobs.txt'): 
	os.remove('jobs.txt')

cmd="qstat > jobs.txt"
subprocess.Popen(cmd,shell=True).wait()

for line in open('jobs.txt','r'): 
	if len(line.split())>4: 
		if line.split()[2] == 'jporta': 
			cmd='qdel %s' %(line.split()[0]	)
			subprocess.Popen(cmd,shell=True).wait()

