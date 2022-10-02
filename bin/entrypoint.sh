#!/usr/bin/env bash

set -ex

yes | otree resetdb
echo 'yes' | otree collectstatic

otree runhftserver 0.0.0.0:8000
