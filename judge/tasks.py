# Judge v0.1 - tasks.py
# Author: Ryan Cobb (@cobbr_io)
# Project Home: https://github.com/cobbr/Judge
# License: GNU GPLv3

from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded

# Import utility libraries for various poller services
from urlparse import urlparse
from ftplib import FTP
import dns.resolver, requests, difflib, poplib
from dns.exception import DNSException
from StringIO import StringIO
from smtplib import SMTP
import os.path
from time import sleep

from db import execute_db_query

app = Celery('tasks', broker='amqp://')
app.config_from_object('config')

s = requests.session()
timeout = app.conf['POLL_TIMEOUT']

def poll():
    """
    Iterates over all the active services in the database and attempt to execute that service's functionality. The success or failure of the service and any error messages are stored in the database.
    """
    for service in execute_db_query('select * from service where service_active = 1'):
        sleep(2)
        # Grab the service from the database
        row = execute_db_query('select * from service_type join service ON (service_type.service_type_id = service.service_type_id) where service.service_type_id = ?', [service['service_type_id']])[0]
        if row:
            type = row['service_type_name']
            # Perform DNS Request
            if type == 'dns':
                poll_dns.delay(timeout, service['service_id'], service['service_connection'], service['service_request'])
            # Perform HTTP(S) Request
            elif type == 'http' or type == 'https':
                poll_web.delay(timeout, service['service_id'], row['service_type_name'], service['service_connection'], service['service_request'],type)
            # Perform FTP Request
            elif type == 'ftp':
                poll_ftp.delay(timeout, service['service_id'], service['service_connection'], service['service_request'])
            # Perform SMTP request to send mail, POP3 to retrieve it back
            elif type == 'mail':
                poll_mail.delay(timeout, service['service_id'], service['service_connection'], service['service_request'])

@app.task(soft_time_limit=6)
def poll_dns(poll_timeout, service_id, service_connection, service_request):
    try:
        try:
            result = ''
            try:
                resolv = dns.resolver.Resolver()
                resolv.nameservers = [service_connection]
                resolv.timeout = poll_timeout
                resolv.lifetime = poll_timeout
                answers = resolv.query(service_request, 'TXT')
                for rdata in answers:
                    result += rdata.to_text().lower()
                print(result)
            except DNSException:
                execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'DNS Timeout on request for: ' + service_request + ' using server: ' + service_connection])
            match = False
            for team in execute_db_query('select * from team'):
                if team['team_name'].lower() in result:
                    execute_db_query('insert into poll(poll_score, service_id, team_id, service_type_name) values(1,?,?,?)', [service_id,team['team_id'],"dns"]);
                    match = True
                    break
            if not match:
                execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(1,?,?)', [service_id,"dns"])

        except Exception as e:
            execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'DNS Request resulted in exception: ' + repr(e)])
            execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(1,?,?)', [service_id,"dns"])
            pass
    except SoftTimeLimitExceeded:
        execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'Task timed out. No error message received.'])
        execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(1,?,?)', [service_id,"dns"])

@app.task(soft_time_limit=6)
def poll_web(poll_timeout, service_id, service_type, service_connection, service_request,type1):
    try:
        try:
            try:
                result = s.get(service_type + '://' + service_connection + service_request, timeout=poll_timeout, verify=False).text
            except requests.exceptions.Timeout as e:
                execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'HTTP(S) Request resulted in a Timeout exception: ' + repr(e)])
                execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(1,?,?)', [service_id,type1])
                return
            except requests.exceptions.ConnectionError as e:
                execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'HTTP(S) Request resulted in a ConnectionError exception: ' + repr(e) + '. This could be thre result of DNS failure, a refused connection, etc.'])
                execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(1,?,?)', [service_id,type1])
                return
            except requests.exceptions.HTTPError as e:
                execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'HTTP(S) Request resulted in a HTTPError exception: ' + repr(e) + '. This means the HTTP response returned an unsuccessful status code.'])
                execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(1,?,?)', [service_id,type1])
                return
            except requests.exceptions.TooManyRedirects as e:
                execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'HTTP(S) Request resulted in a TooManyRedirects exception: ' + repr(e)])
                execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(1,?,?)', [service_id,type1])
                return
            except requests.exceptions.RequestException as e:
                execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'HTTP(S) Request resulted in an unknown request exception: ' + repr(e)])
                execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(1,?,?)', [service_id,type1])
                return
            match = False
            for team in execute_db_query('select * from team'):
                if team['team_name'] in result:
                    execute_db_query('insert into poll(poll_score, service_id, team_id, service_type_name) values(1,?,?,?)', [service_id,team['team_id'],type1]);
                    match = True
                    break
            if not match:
                execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(1,?,?)', [service_id,type1])
        except Exception as e:
            execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'HTTP(S) Request resulted in exception: ' + repr(e)])
            execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(1,?,?)', [service_id,type1])
            pass
    except SoftTimeLimitExceeded:
        execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'Task timed out. No error message received.'])
        execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(1,?,?)', [service_id,type1])

# TODO: improved exception handling for FTP
@app.task(soft_time_limit=6)
def poll_ftp(poll_timeout, service_id, service_connection, service_request):
    try:
        try:
            match = False
            ftp = FTP(host=service_connection, timeout=(poll_timeout*2))
            ftp_headers = ftp.getwelcome()
            
            for team in execute_db_query('select * from team'):
                if team['team_name'] in ftp_headers:
                    execute_db_query('insert into poll(poll_score,service_id,team_id,service_type_name) values(1,?,?,?)', [service_id,team['team_id'],'ftp'])
                    match = True
                    break
            if not match and ftp_headers:
                execute_db_query('insert into poll(poll_score,service_id,service_type_name) values(1,?,?)', [service_id,'ftp'])
        except Exception as e:
            execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'FTP request resulted in exception: ' + repr(e)])
            execute_db_query('insert into poll(poll_score,service_id,service_type_name) values(1,?,?)', [service_id,'ftp'])
            return
    except SoftTimeLimitExceeded:
        execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'Task timed out. No error message received.'])
        execute_db_query('insert into poll(poll_score,service_id,service_type_name) values(1,?,?)', [service_id,'ftp'])

# TODO: Improved exception handling for mail
@app.task(soft_time_limit=6)
def poll_mail(poll_timeout, service_id, service_connection, service_request):
    try:
        match = False
        try:
            smtpServer=SMTP(service_connection,timeout=(poll_timeout*2))
            smtp_headers = smtpServer.helo(service_connection)
            for team in execute_db_query('select * from team'):
                if team['team_name'].lower() in smtp_headers[1].lower():
                    execute_db_query('insert into poll(poll_score, service_id, team_id, service_type_name) values(1,?,?,?)', [service_id,team['team_id'],'mail'])
                    match = True
                    break
        except Exception as e:
            execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'SMTP Request resulted in exception: ' + repr(e)])
            execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(0,?,?)', [service_id,'mail'])
            return
        if not match:
            execute_db_query('insert into poll(poll_score, service_id, service_type_name) values(1,?,?)', [service_id,'mail'])
    except SoftTimeLimitExceeded:
        execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'Task timed out. No error message received.'])
        execute_db_query('insert into poll(poll_score,service_id,service_type_name) values(1,?,?)', [service_id,'mail'])
