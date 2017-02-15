# Judge v0.1 - reset.ps1
# Author: Ryan Cobb (@cobbr_io)
# Project Home: https://github.com/cobbr/Judge
# License: GNU GPLv3

python -m celery -A judge.tasks purge -f
$env:FLASK_APP = "judge/judge.py"
python -m flask setup
python -m flask populate
