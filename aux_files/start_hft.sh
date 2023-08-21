#!/bin/bash

# Set PYENV_ROOT and ensure it's in the PATH
export PYENV_ROOT="/home/hft_dev/.pyenv"

# Conditionally update the PATH
if [[ ":$PATH:" != *":$PYENV_ROOT/bin:"* ]]; then
    export PATH="$PYENV_ROOT/bin:$PATH"
fi
if [[ ":$PATH:" != *":$PYENV_ROOT/shims:"* ]]; then
    export PATH="$PYENV_ROOT/shims:$PATH"
fi


# Initialize pyenv
eval "$(pyenv init -)"

#set local python
cd /home/hft_dev/high_frequency_trading
pyenv local 3.6.15/envs/pyenv_exchange_server

# Activate the desired pyenv environment
pyenv activate 3.6.15/envs/pyenv_exchange_server

# Move to the desired directory
cd /home/hft_dev/high_frequency_trading

# Set and use the otree executable
export OTREE_EXECUTABLE="/home/hft_dev/.pyenv/versions/pyenv_exchange_server/bin/otree"
python3 manage.py collect_exg_config
$OTREE_EXECUTABLE devserver 0.0.0.0:8000

echo "Script finished"
