#!/usr/bin/bash

############################################################################
# This script checks whether a port is OPEN or CLOSED on a specificed host #
# Usage: ./check_open_port.sh [host] [port]                                #
# Usage: ./check_open_port.sh 192.168.1.131 53                             #
############################################################################

check_port() {
  local host=$1
  local port=$2
  timeout 1 bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null
  if [ $? -eq 0 ]; then
    echo "Port $port on $host is OPEN"
  else
    echo "Port $port on $host is CLOSED or FILTERED"
  fi
}

# Take user input
read -p "Enter target host IP or hostname: " TARGET_HOST
read -p "Enter port(s) to check (e.g., 80, 22, 8080-8085): " PORTS_TO_CHECK

# Handle single port, comma-separated ports, or port ranges
if [[ "$PORTS_TO_CHECK" =~ "-" ]]; then
  IFS='-' read -r start_port end_port <<< "$PORTS_TO_CHECK"
  for (( port=start_port; port<=end_port; port++ )); do
    check_port "$TARGET_HOST" "$port"
  done
elif [[ "$PORTS_TO_CHECK" =~ "," ]]; then
  IFS=',' read -ra ports_array <<< "$PORTS_TO_CHECK"
  for port in "${ports_array[@]}"; do
    check_port "$TARGET_HOST" "$port"
  done
else
  check_port "$TARGET_HOST" "$PORTS_TO_CHECK"
fi
