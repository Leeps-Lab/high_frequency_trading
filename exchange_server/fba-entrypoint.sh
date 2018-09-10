if [ "$#" -gt 3 ]; then
        echo "usage: ./run_fba_groups.sh [num_groups] [batch_length] [flag]"
        exit 1
fi

groups=$(($1-1))
timestamp=$(date +'%Y-%m-%d_%H:%M:%S')
batch=$2
flag=$3

./stop_all.sh

if [ -z "$1" ];
then
	groups=1
fi

i="0"

while [ "$i" -lt "$groups" ]
do
mkdir -p fba_data
ls
python3 run_exchange_server.py --host 0.0.0.0 --port 900$i --mechanism fba --interval ${batch}  --book_log fba_data/${timestamp}_group_$i.log --${flag} &
i=$(($i+1))
done && python3 run_exchange_server.py --host 0.0.0.0 --port 900$i --mechanism fba --interval ${batch}   --book_log fba_data/${timestamp}_group_$i.log --${flag}
