#!/usr/bin/bash

echo "System Information:"
echo "-------------------"
echo "Hostname: $(hostname)"
echo "Kernel Version: $(uname -r)"
echo "Uptime: $(uptime -p)"
echo "Disk Usage:"
df -h
echo "Memory Usage:"
free -h
