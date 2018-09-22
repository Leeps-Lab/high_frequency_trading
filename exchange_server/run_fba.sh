#!/bin/bash

timestamp=$(date +'%Y-%m-%d_%H:%M:%S')
port=$1
interval=$2

mkdir -p FBA_DATA
python3 run_exchange_server.py --host 0.0.0.0 --port ${port} --mechanism fba \
--interval ${interval} --book_log FBA_DATA/${timestamp}_port_${port}.log
