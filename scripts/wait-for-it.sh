#!/usr/bin/env bash
# Simplified wait-for-it.sh
host=$(echo $1 | cut -d: -f1)
port=$(echo $1 | cut -d: -f2)
timeout=${3:-30}

echo "Waiting for $host:$port..."
for i in $(seq 1 $timeout); do
  if nc -z $host $port >/dev/null 2>&1 || (echo > /dev/tcp/$host/$port) >/dev/null 2>&1; then
    echo "$host:$port is available."
    exit 0
  fi
  sleep 1
done
echo "Timeout waiting for $host:$port."
exit 1
