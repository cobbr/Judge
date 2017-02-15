#!/bin/bash
# Judge v0.1 - judge.sh
# Author: Ryan Cobb (@cobbr_io)
# Project Home: https://github.com/cobbr/Judge
# License: GNU GPLv3

celery -A judge.tasks worker -n celery@localhost -c 5 --loglevel=info > /dev/null 2>&1 &
python run.py
