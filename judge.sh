#!/bin/bash

celery -A judge.tasks worker -n celery@localhost -c 5 --loglevel=info > /dev/null 2>&1 &
python run.py
