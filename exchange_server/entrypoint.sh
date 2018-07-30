if [ "$#" -ne 1 ]; then
        echo "usage: ./run_cda_groups.sh [num_groups] [flag]"
        exit 1
fi

groups=$(($1-1))
timestamp=$(date +'%Y-%m-%d_%H:%M:%S')
flag=$2

./stop_all.sh

if [ -z "$1" ];
then
	groups=1
fi

i="0"

while [ "$i" -lt "$groups" ]
do
mkdir -p CDA_DATA
python3 run_exchange_server.py --host 0.0.0.0 --port 900$i --mechanism cda  --book_log CDA_DATA/${timestamp}_group_$i.log --${flag} &
i=$(($i+1))
done && python3 run_exchange_server.py --host 0.0.0.0 --port 900$i --mechanism cda  --book_log CDA_DATA/${timestamp}_group_$i.log --${flag}
