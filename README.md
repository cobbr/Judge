# Judge

This project is designed to be a simple, but useful way to quickly debug services on a CCDC (Collegiate Cyber Defense Competition) network.

Judge is a python Flask web application that can be run on Windows or Linux. Services expected to be running within a network environment are added via a web interface,
and these chosen services are continually polled for functionality. A score is tallied based upon results and displayed in a scoreboard on the web interface.

The main advantage of Judge is that it provides detailed information about what tests are failing and why, allowing a team
to quickly discover and diagnose service issues.

## Services

Judge currently supports testing of the following services:
* HTTP(S)
* FTP
* DNS
* Mail (SMTP for sending emails, POP3 to retrieve mail)


----
Judge is developed as a tool for Baylor's National Collegiate Cyber Defense Competition team.
