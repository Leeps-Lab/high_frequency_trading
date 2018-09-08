#!/bin/bash

if [ "$#" -ne 2 ]; then
        echo "usage: ./run_cda_groups.sh [num_groups] [flag]"
        exit 1
fi

groups=$1
timestamp=$(date +'%Y-%m-%d_%H:%M:%S')
interval=$2


if [ -z "$1" ];
then
	groups=1
fi

for i in `seq $groups`;
do
	mkdir -p FBA_DATA
	python3 run_exchange_server.py --host 0.0.0.0 --port 910$i --mechanism fba \
    --interval ${interval} --book_log FBA_DATA/${timestamp}_group_$i.log --debug &
done
