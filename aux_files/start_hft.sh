#!/bin/bash

# Activate the pyenv environment
export PYENV_ROOT="/home/hft_dev/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"

eval "$(pyenv init --path)"

#source /home/hft_dev/.pyenv/bin/pyenv
#/home/hft_dev/.pyenv/bin/pyenv activate pyenv_exchange_server
pyenv activate 3.6.15/envs/pyenv_exchange_server

# Run your high-frequency trading command
cd /home/hft_dev/high_frequency_trading

export OTREE_EXECUTABLE="/home/hft_dev/.pyenv/versions/pyenv_exchange_server/bin/otree"
#$OTREE_EXECUTABLE resetdb
#$OTREE_EXECUTABLE makemigrations
#$OTREE_EXECUTABLE migrate

python3 manage.py collect_exg_config

$OTREE_EXECUTABLE devserver 0.0.0.0:8000

echo "Script finished"
