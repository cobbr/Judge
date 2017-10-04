# Judge v0.1 - install.sh
# Author: Ryan Cobb (@cobbr_io)
# Project Home: https://github.com/cobbr/Judge
# License: GNU GPLv3

if [[ "$(pwd)" != *setup ]]
then
    cd ./setup
fi
sudo apt-get install python-pip rabbitmq-server -y
sudo pip install -r requirements.txt
cd ..
export FLASK_APP=judge/judge.py
flask setup
flask populate
