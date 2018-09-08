#! /bin/bash

die() {
    printf '%s\n' "$1" >&2
    exit 1
}

USAGE="Script to run high frequency experiments in otree.
Usage: $0 ... [option] [arg] ...
-m  --markets NUM_MARKETS  Number of separete matching engines to run.
-b  --build    Recreates images.
-p  --pull     Downloads updates from git repo. Useful if new configs are available.  
-w  --workers NUM_WORKERS  Number of worker threads to start under main process.
"


num_markets="1"
batch_length="3" 

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
        -t|--batch-length)
            if [ "$2" ]; then
                batch_length="$2"
                shift
            else
                die "ERROR: --batch-length requires an argument."
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

export BATCH_LENGTH="$batch_length" 
export NUM_GROUPS="$num_markets"

echo "starting exchanges with cda and fba formats.
fba exchanges will have batch length of $batch_length."

if [ "$build" ];then
    docker-compose up --build
else
    docker-compose up
fi




