#!/bin/bash

# Activate the pyenv environment
export PYENV_ROOT="/home/hft_dev/.pyenv"
if [[ ":$PATH:" != *":$PYENV_ROOT/bin:"* ]]; then
    export PATH="$PYENV_ROOT/bin:$PATH"
fi


eval "$(pyenv init -)"

#source /home/hft_dev/.pyenv/bin/pyenv
#/home/hft_dev/.pyenv/bin/pyenv activate pyenv_exchange_server
pyenv activate 3.6.15/envs/pyenv_exchange_server

# Run your high-frequency trading command
cd /home/hft_dev/exchange_server

#$EXCHANGE_EXECUTABLE
python3 run_exchange_server.py --host 0.0.0.0 --port 9001 --debug --mechanism cda
