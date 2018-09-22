#!/bin/bash

timestamp=$(date +'%Y-%m-%d_%H:%M:%S')
port=$1

mkdir -p cda_data
python3 run_exchange_server.py --host 0.0.0.0 --port ${port} --mechanism cda  --book_log cda_data/${timestamp}_port_${port}.log

