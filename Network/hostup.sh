#!/usr/bin/bash

# Script to detect running machines on a network segment

for i in $(seq 2 254); do
    # This script is done for the 192.168.1.x segment
    timeout 1 bash -c "ping -c 1 192.168.1.$i > /dev/null 2>&1" && echo "Host 192.168.1.$i - ACTIVE" & 
done; wait 
