# Judge v0.1 - reset.sh
# Author: Ryan Cobb (@cobbr_io)
# Project Home: https://github.com/cobbr/Judge
# License: GNU GPLv3

celery -A judge.tasks purge -f
export FLASK_APP=judge/judge.py
flask setup
flask populate
