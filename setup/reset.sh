celery -A tasks purge -f
export FLASK_APP=judge/judge.py
flask setup
flask populate
