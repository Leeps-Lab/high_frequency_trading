#!/bin/bash

if [ "$#" -ne 1 ]; then
        echo "usage: ./run_cda_groups.sh [num_groups] [flag]"
        exit 1
fi

groups=$1
timestamp=$(date +'%Y-%m-%d_%H:%M:%S')
flag=$2


if [ -z "$1" ];
then
	groups=1
fi

for i in `seq $groups`;
do
	mkdir -p cda_data
	python3 run_exchange_server.py --host 0.0.0.0 --port 900$i --mechanism cda  --book_log cda_data/${timestamp}_group_$i.log --${flag} &
done
