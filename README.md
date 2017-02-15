# Judge

Judge is a scoreboard and debugging tool designed for use on a CCDC (Collegiate Cyber Defense Competition) network. It can be used during practice sessions to quickly debug failing services or in competition to keep score for teams.

CCDC (or similar competitions) are usually scored upon keeping services functional within a business network. Services expected to be running on a network can be communicated to Judge through a simple YAML configuration file or configured through the web interface (shown below).

In addition to functioning as a scorer, Judge also provides detailed error messages on why particular services are failing, allowing a team to quickly discover and debug a failing service (shown below).

Judge is implemented as a python Flask web application, compatible with Linux and Windows. If you plan on running Judge as an official scorer for a competition you should read the production notes available here.

### Services

Judge currently supports testing of the following services:
* HTTP(S)
* FTP
* DNS
* SMTP
* POP3

## Installation

Judge is designed to require minimal installation time, so it could be used without any configuration/setup time by a team in the middle of a competition.

It is always recommended to run Judge on a Linux system if at all possible. Installation is quicker, and Judge is more stable when run on a Linux system. Windows compatiblity is maintained as a necessity in the event that a Linux system is not available.

Installation is simple on a Linux system:
```
$ git clone https://github.com/cobbr/Judge
$ cd Judge
$ ./setup/install.sh
```

The commands for installation on Windows is just as simple, however dependencies can be problematic. Judge is dependent on python. It assumes that it is already installed, and that python.exe is added to your PATH. Be sure python is setup correctly before attempting to install Judge. Judge is also dependent on Erlang and RabbitMQ (Judge uses the python celery package for forking background processes which requires these programs), and it **will** attempt to download and install them upon execution of Judge's install script:

```
PS> git clone https://github.com/cobbr/Judge
PS> cd Judge
PS> ./setup/install.ps1
```

## Configuration

Judge can be configured in two ways. The simplest is through the web interface, post-launch. However, a team in the middle of a competition may not want to spend the time to individually configure every service. And a competition administrator needs to be sure that all services are launched at the same time, to ensure fair scoring.

For these reasons, Judge provides a way to configure services pre-launch by editing the `services.yaml` configuration file with pre-defined services.

Judge ships with a default `services.yaml` that illustrates it's use. Here is a small subset of that example:
```
teams:
  - team_name : Baylor

services:
  # Available service_types are: dns, http, https, ftp, mail
  - service_type_name       : dns
  # The team that should be scored based on the functionality of this service
    team_name               : Baylor
  # A name for this service, will be displayed on the scoreboard
    service_name            : internal dns - addns.ccdc.local
  # The server IP that will be queried for this service
    service_connection      : 172.25.21.27
  # The domain name that this service is querying
    service_request         : addns.ccdc.local
  # The expected result the server should return, service will fail if result does not match expected
    service_expected_result : 172.25.21.27
  - service_type_name       : http
    team_name               : Baylor
    service_name            : internal http - web.ccdc.local
    service_connection      : 172.25.21.3
    service_request         : /
  # The name of the file on the server that we will compare the result of the request to, the result must match
    service_expected_result : data/uploads/default/iis-85.html
```

## Launch

Finally, run the application:

Linux
```
$ ./judge.sh
```

Windows
```
PS> ./judge.ps1
```

Scoring history is saved, even after Judge has stopped running, and will be resume upon re-launch. You can reset scoring at any time by running:

(Note: This will also remove any configurations added through the web interface, only the `services.yaml` configurations will remain.)

Linux
```
$ ./setup/reset.sh
```

Windows
```
PS> ./setup/reset.ps1
```

## Issues/Contributions

Contributions are welcome!

Please report all bugs through Github issues. If you have ideas for additional features or want to implement your own, also add these through Github issues.
