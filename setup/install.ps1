$scriptPath = Split-Path (Get-Variable MyInvocation).Value.MyCommand.Path
python -m pip install -r $scriptPath\requirements.txt
(new-object System.Net.WebClient).DownloadFile("https://www.erlang.org/downloads/otp_win64_19.2.exe", "otp_win64_19.2.exe")
.\otp_win64_19.2.exe
rm otp_win64_19.2.exe
(new-object System.Net.WebClient).DownloadFile("https://www.rabbitmq.com/releases/rabbitmq-server/v3.6.6/rabbitmq-server-3.6.6.exe", "rabbitmq-server-3.6.6.exe")
.\rabbitmq-server-3.6.6.exe
rm rabbitmq-server-3.6.6.exe
$env:FLASK_APP = "judge/judge.py"
python -m flask setup
python -m flask populate
