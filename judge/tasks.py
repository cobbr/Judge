from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded

# Import utility libraries for various poller services
from urlparse import urlparse
from ftplib import FTP
import dns.resolver, requests, difflib, smtplib, poplib
from dns.exception import DNSException
from StringIO import StringIO

import os.path
from time import sleep

from db import execute_db_query

app = Celery('tasks', broker='amqp://')
app.config_from_object('config')

s = requests.session()

def poll():
    """
    Iterates over all the active services in the database and attempt to execute that service's functionality.
    The success or failure of the service and any error messages are stored in the database.
    """
    for service in execute_db_query('select * from service where service_active = 1'):
        # Grab the service from the database
        row = execute_db_query('select * from service_type join service ON (service_type.service_type_id = service.service_type_id) where service.service_type_id = ?', [service['service_type_id']])[0]
        if row:
            type = row['service_type_name']
            # Perform DNS Request
            if type == 'dns':
                poll_dns(service['service_id'], service['service_connection'], service['service_request'], service['service_expected_result'])
            # Perform HTTP(S) Request
            elif type == 'http' or type == 'https':
                poll_web(service['service_id'], row['service_type_name'], service['service_connection'], service['service_request'], service['service_expected_result'])
            # Perform FTP Request
            elif type == 'ftp':
                poll_ftp(service['service_id'], service['service_connection'], service['service_request'], service['service_expected_result'])
            # Perform SMTP request to send mail, POP3 to retrieve it back
            elif type == 'mail':
                poll_mail(service['service_id'], service['service_connection'], service['service_request'], service['service_expected_result'])

def poll_dns(service_id, service_connection, service_request, service_expected_result):
    try:
        try:
            result = ''
            try:
                resolv = dns.resolver.Resolver()
                resolv.nameservers = [service_connection]
                resolv.timeout = app.conf['POLL_TIMEOUT']
                resolv.lifetime = app.conf['POLL_TIMEOUT']
                answers = resolv.query(service_request, 'A')
                for rdata in answers:
                    result = rdata.to_text()
            except DNSException:
                execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'DNS Timeout on request for: ' + service_request + ' using server: ' + service_connection])
            if result == service_expected_result:
                execute_db_query('insert into poll(poll_score,service_id) values(1,?)', [service_id])
            else:
                execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'DNS Request result: ' + result + ' did not match expected: ' + service_expected_result])
                execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
        except Exception as e:
                execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'DNS Request resulted in exception: ' + repr(e)])
                execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
                pass
    except SoftTimeLimitExceeded:
        execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'Task timed out. No error message received.'])
        execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])

def poll_web(service_id, service_type, service_connection, service_request, service_expected_result):
    try:
        try:
            try:
                result = s.get(service_type + '://' + service_connection + service_request, timeout=app.conf['POLL_TIMEOUT'], verify=False).text
            except requests.exceptions.Timeout as e:
                execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'HTTP(S) Request resulted in a Timeout exception: ' + repr(e)])
                execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
                return
            except requests.exceptions.ConnectionError as e:
                execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'HTTP(S) Request resulted in a ConnectionError exception: ' + repr(e) + '. This could be thre result of DNS failure, a refused connection, etc.'])
                execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
                return
            except requests.exceptions.HTTPError as e:
                execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'HTTP(S) Request resulted in a HTTPError exception: ' + repr(e) + '. This means the HTTP response returned an unsuccessful status code.'])
                execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
                return
            except requests.exceptions.TooManyRedirects as e:
                execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'HTTP(S) Request resulted in a TooManyRedirects exception: ' + repr(e)])
                execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
                return
            except requests.exceptions.RequestException as e:
                execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'HTTP(S) Request resulted in an unknown request exception: ' + repr(e)])
                execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
                return
            match = False
            if os.path.isfile(service_expected_result):
                upload = open(service_expected_result, 'r')
                service_expected_result = upload.read()
                upload.close()
                # Only comparing first 10 lines for now. Have no good way to compare dynamic portions of a webpage.
                one = service_expected_result.splitlines(0)[0:10]
                two = result.splitlines(0)[0:10]
                if one == two:
                    match = True
                else:
                    diff = difflib.unified_diff(one, two)
                    execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'HTTP(S) Request result did not match expected. Diff: \n' + ''.join(diff)])
            else:
                execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'Local filename for expected result: ' + service_expected_result + ' does not exist.'])
            if match:
                execute_db_query('insert into poll(poll_score,service_id) values(1,?)', [service_id])
            else:
                execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
        except Exception as e:
            execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'HTTP(S) Request resulted in exception: ' + repr(e)])
            execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
            pass
    except SoftTimeLimitExceeded:
        execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'Task timed out. No error message received.'])
        execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])

# TODO: improved exception handling for FTP
def poll_ftp(service_id, service_connection, service_request, service_expected_result):
    try:
        try:
            match = False
            ftp = FTP(host=service_connection, timeout=(app.conf['POLL_TIMEOUT']*2))
            ftp.login()
            resultStringIO = StringIO()
            ftp.retrbinary('RETR ' + service_request, resultStringIO.write)
            result = resultStringIO.getvalue()
            if os.path.isfile(service_expected_result):
                upload = open(service_expected_result, 'r')
                service_expected_result = upload.read()
                upload.close()
                if result == service_expected_result:
                    match = True
                else:
                    diff = difflib.unified_diff(service_expected_result, result)
                    execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'FTP Request result did not match expected. Diff: \n' + ''.join(diff)])
            else:
                execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'Local filename for expected result: ' + service_expected_result + ' does not exist.'])
            if match:
                execute_db_query('insert into poll(poll_score,service_id) values(1,?)', [service_id])
            else:
                execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
        except Exception as e:
            execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'FTP request resulted in exception: ' + repr(e)])
            execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
            pass
    except SoftTimeLimitExceeded:
        execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'Task timed out. No error message received.'])
        execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])

# TODO: Improved exception handling for mail
def poll_mail(service_id, service_connection, service_request, service_expected_result):
    try:
        try:
            sender = service_request.split(',')[0]
            recipient = service_request.split(',')[1]
            msg = service_request.split(',')[2]

            sender_user = sender.split(':')[0]
            sender_pass = sender.split(':')[1].split('@')[0]
            sender = sender_user + '@' + sender.split('@')[1]
            try:
                smtpServer = smtplib.SMTP(service_connection,timeout=(app.conf['POLL_TIMEOUT']*2))
                smtpServer.sendmail(sender,recipient,msg)
                smtpServer.quit()
            except Exception as e:
                execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'SMTP Request resulted in exception: ' + repr(e)])
                execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
                return
            match = False
            try:
                Mailbox = poplib.POP3(service_connection, timeout=(app.conf['POLL_TIMEOUT']*2))
                Mailbox.user(sender_user)
                Mailbox.pass_(sender_pass)
                numMessages = len(Mailbox.list()[1])
                if numMessages < 1:
                    execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'POP3 Request returned an empty mailbox. SMTP send or POP3 receive may have failed.'])
                else:
                    # Retrieve only the latest message
                    message = Mailbox.retr(numMessages)[1]
                    result = message[-1]
                    if result == service_expected_result:
                        match = True
                    else:
                        diff = difflib.unified_diff(service_expected_result, result)
                        execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'POP3 response did not match expected result. Diff: \n' + ''.join(diff)])
            except Exception as e:
                execute_db_query('insert into error(service_id,error_message) values(?,?)', [service_id, 'POP3 Request resulted in exception: ' + repr(e)])
                pass
            if match:
                execute_db_query('insert into poll(poll_score,service_id) values(1,?)', [service_id])
            else:
                execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
        except Exception as e:
            execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'Mail request resulted in exception: ' + repr(e)])
            execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
            pass
    except SoftTimeLimitExceeded:
        execute_db_query('insert into error(service_id, error_message) values(?,?)', [service_id, 'Task timed out. No error message received.'])
        execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [service_id])
