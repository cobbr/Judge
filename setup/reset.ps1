celery -A tasks purge -f
$env:FLASK_APP = "judge/judge.py"
python -m flask setup
python -m flask populate
