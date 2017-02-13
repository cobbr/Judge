$scriptPath = Split-Path (Get-Variable MyInvocation).Value.MyCommand.Path
python -m pip install -r $scriptPath\requirements.txt
# This is stolen from: http://stackoverflow.com/questions/31712686/how-to-check-if-a-program-is-installed-and-install-it-if-it-is-not
function Get-InstalledApps
{
    if ([IntPtr]::Size -eq 4) {
        $regpath = 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
    }
    else {
        $regpath = @(
            'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
            'HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
        )
    }
    Get-ItemProperty $regpath | .{process{if($_.DisplayName -and $_.UninstallString) { $_ } }} | Select DisplayName, Publisher, InstallDate, DisplayVersion, UninstallString |Sort DisplayName
}

$result = Get-InstalledApps | where {$_.DisplayName -like "*Erlang*"}
If ($result -eq $null) {
   Write-Host "Path: $scriptPath\otp_win64_19.2.exe"
   if (-Not (Test-Path $scriptPath\otp_win64_19.2.exe)) {
       Write-Host "Downloading Erlang..."
       (new-object System.Net.WebClient).DownloadFile("http://erlang.org/download/otp_win64_19.2.exe", $scriptPath + "\otp_win64_19.2.exe")
   }
   Write-Host "Installing Erlang..."
   Start-Process -FilePath $scriptPath\otp_win64_19.2.exe -wait
   rm $scriptPath\otp_win64_19.2.exe
}

$result = Get-InstalledApps | where {$_.DisplayName -like "*RabbitMQ*"}
If ($result -eq $null) {
   If (-Not (Test-Path $scriptPath\rabbitmq-server-3.6.6.exe)) {
       Write-Host "Downloading RabbitMQ..."
       (new-object System.Net.WebClient).DownloadFile("https://www.rabbitmq.com/releases/rabbitmq-server/v3.6.6/rabbitmq-server-3.6.6.exe", $scriptPath  + "\rabbitmq-server-3.6.6.exe")
   }
   Write-Host "Installing RabbitMQ..."
   Start-Process -FilePath $scriptPath\rabbitmq-server-3.6.6.exe -wait
   rm $scriptPath\rabbitmq-server-3.6.6.exe
}

$env:FLASK_APP = "judge/judge.py"
python -m flask setup
python -m flask populate
