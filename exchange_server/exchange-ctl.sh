#!/bin/bash

cmd=$1
groups=$2
timestamp=$(date +'%Y-%m-%d_%H:%M:%S')

for i in `seq $groups`;
do	
	sudo systemctl ${cmd} cda_exchange@900$i.service
	sudo systemctl ${cmd} fba_exchange@910$i.service
done
