# CCDC-Debugger

This project is designed to be a simple, but useful way to quickly debug services on a CCDC (Collegiate Cyber Defense Competition) network.

CCDC-Debugger is a python Flask web application. Services expected to be running within a network environment can be added via the web interface,
and these chosen services will continually be polled. A score will be tallied based upon results. 

The main advantage of the Debugger is that it provides detailed information about what tests are failing and why, allowing a team
to quickly diagnose service issues.

## Services

The Debugger currently supports testing of the following services:
* HTTP
* HTTPS
* FTP
* DNS


----
It was originally developed as a tool for Baylor's National Collegiate Cyber Defense Competition team.
