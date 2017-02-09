#!/bin/bash

celery -A judge.tasks worker -n celery@localhost --loglevel=info &
python run.py
