if [[ "$(pwd)" != *setup ]]
then
    cd ./setup
fi
pip install -r requirements.txt
cd ..
export FLASK_APP=debugger.py
flask setup
flask populate
