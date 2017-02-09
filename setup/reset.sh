celery -A judge.tasks purge -f
export FLASK_APP=judge/judge.py
flask setup
flask populate
