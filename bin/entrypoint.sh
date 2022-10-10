#!/usr/bin/env bash

set -ex

if [ ! -f ~/.hasrun ]; then
    echo 'reset db..'
    yes | otree resetdb

    echo 'read configuration files..'
    python manage.py collect_exg_config

    echo 'collect static files..'
    yes | otree collectstatic

    touch ~/.hasrun
fi

otree runhftserver 0.0.0.0:8000
