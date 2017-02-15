# Judge v0.1 - install.sh
# Author: Ryan Cobb (@cobbr_io)
# Project Home: https://github.com/cobbr/Judge
# License: GNU GPLv3

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
