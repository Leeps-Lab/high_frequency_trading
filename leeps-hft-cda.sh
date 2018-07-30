#! /bin/bash

die() {
    printf '%s\n' "$1" >&2
    exit 1
}

USAGE="Script to run high frequency experiments in otree.
Usage: $0 ... [option] [arg] ...
REQUIRED
-m  --markets NUM_MARKETS  Number of separete matching engines to run.
OPTIONAL
-b  --build    Recreates images.
-p  --pull     Downloads updates from git repo. Useful if new configs are available.  
-w  --workers NUM_WORKERS  Number of worker threads to start under main process.
"

num_workers="4" 
num_markets="1"

while true; do
    case $1 in
        -h|\?|--help)
            echo "$USAGE"
            exit
            ;;
        -b|--build)
            echo "--build triggered, will recreate images."
            build=1
            ;;
        -p|--pull)
            echo "--pull triggered, will pull from remote."
            pull=1
            ;;
        -w| --workers)
            if [ "$2" ]; then
                num_workers="$2"
                shift
            else
                die "ERROR: --workers requires an argument."
            fi
            ;;
        -m|--markets)
            if [ "$2" ]; then
                num_markets="$2"
                shift
            else
                die "ERROR: --markets requires an argument."
            fi
            ;;
        -?*)
            die "ERROR: Unknown option."
            ;;
         *)
            break
    esac
    shift
done

export NUM_WORKERS="$num_workers" 
export NUM_GROUPS="$num_markets"

echo "starting HFT experiment.
otree server will have $num_workers workers. 
$num_markets markets will be trading. "

if [ "$pull" ]; then
    git pull origin master
fi

if [ "$build" ];then
    docker-compose up --build
else
    docker-compose up
fi







