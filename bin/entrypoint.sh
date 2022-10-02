#!/usr/bin/env bash

set -ex

yes | otree resetdb
yes | otree collectstatic

otree runhftserver 0.0.0.0:8000
