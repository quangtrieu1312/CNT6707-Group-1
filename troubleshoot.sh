#!/usr/bin/env bash
if [ $# -ne 1 ]; then
	echo "Usage: $0 <mininet host>"
	echo "Example: $0 S"
	exit 1
fi

grepString="mininet:$1[^a-zA-Z0-9]*$"
PID=$(lsns -t net | grep -E $grepString | awk '{print $4}')
[ $? -eq 0 ] || { echo "mininet host $1 doesn't exist"; exit 1; }
echo "entering net namespace of pid=$PID"
nsenter -t $PID -n bash
