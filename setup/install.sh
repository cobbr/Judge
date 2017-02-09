if [[ "$(pwd)" != *setup ]]
then
    cd ./setup
fi
pip install -r requirements.txt
sudo apt-get install rabbitmq-server -y
cd ..
export FLASK_APP=judge/judge.py
flask setup
flask populate
