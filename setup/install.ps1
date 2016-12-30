$scriptPath = Split-Path (Get-Variable MyInvocation).Value.MyCommand.Path
python -m pip install -r $scriptPath\requirements.txt
$env:FLASK_APP = "debugger.py"
python -m flask setup
python -m flask populate