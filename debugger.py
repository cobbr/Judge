#!/usr/bin/python
#
# CCDC-Debugger
# 
# Debugging utility for a CCDC team
#
# Author: Ryan Cobb

# Import python service utilities
from urlparse import urlparse
from ftplib import FTP
import sqlite3, dns.resolver, requests, difflib, smtplib, poplib
from dns.exception import DNSException
from StringIO import StringIO

# import python os libraries
import os.path
from threading import Thread
from time import sleep

# import flask libraries
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, validators
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename

# Application settings
app = Flask(__name__)
app.secret_key = 'dev key'


# Database functions
def database_create():
    """
    Create the backend ./data/debugger.db sqlite database
    """
    db = database_connect()
    with app.open_resource('./data/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def database_populate():
    """
    Populate the database with default data.
    """
    db = database_connect()
    with app.open_resource('./data/default/data.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def database_connect():
    """
    Connect with the backend ./debugger.db sqlite database and return the
    connection object.
    """
    try:
        # set the database connectiont to autocommit w/ isolation level
        conn = sqlite3.connect('./data/debugger.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print "Error connecting to database. Must run 'flask setup' prior to running. Error message: " + str(e)
        sys.exit()

def execute_db_query(query, args=None):
    """
    Execute the supplied query on the provided db conn object
    with optional args for a paramaterized query.
    """
    conn = database_connect()
    cur = conn.cursor()
    if(args):
        cur.execute(query, args)
    else:
        cur.execute(query)
    conn.commit()
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

@app.context_processor
def utility_processor():
    """
    Exports functions that can be used in Jinja HTML templates.
    """
    return dict(execute_db_query=execute_db_query)
       
@app.cli.command('setup')
def setup():
    """
    Flask command line function that creates/resets the database with no data.
    """
    if os.path.isfile('data/debugger.db'):
        os.remove('data/debugger.db')
    print 'Initializing database...'
    database_create()
    print 'Done.'

@app.cli.command('populate')
def populate():
    """
    Flask command line function that populates the database with default data
    """
    print 'Populating database...'
    database_populate()
    print 'Done.'

# WTF-Form classes
# Used to create functional forms for adding/removing services/teams with the Web UI

class AddTeamForm(FlaskForm):
    team_name = StringField('Team Name', [validators.Length(min=1, max=50)])

class AddDNSServiceForm(FlaskForm):
    team_name = SelectField('Team', coerce=int)
    service_name = StringField('Service Name', [validators.Length(min=1, max=50)])
    service_connection = StringField('DNS Server IP', [validators.IPAddress()])
    service_request = StringField('DNS Lookup Hostname', [validators.Length(min=1, max=50)])
    service_expected_result = StringField('Expected IP Result', [validators.IPAddress()])

class AddWebServiceForm(FlaskForm):
    team_name = SelectField('Team')
    service_name = StringField('Service Name', [validators.Length(min=1, max=50)])
    service_url = StringField('HTTP(S)/FTP URL', [validators.URL()])
    service_file = FileField('Expected File', [FileRequired()])

class AddMailServiceForm(FlaskForm):
    team_name = SelectField('Team', coerce=int)
    service_name = StringField('Service Name', [validators.Length(min=1, max=50)])
    service_connection = StringField('Mail Server IP', [validators.IPAddress()])
    from_email = StringField('From', [validators.Length(min=1, max=50)])
    to_email = StringField('To', [validators.Length(min=1, max=50)])
    service_expected_result = StringField('Message', [validators.Length(min=1,max=200)])


# Flask web functionality
@app.route('/configure', methods=['GET'])
def configure(): 
    """
    The configure page is used to add/remove teams/services.
    """
    forms = {}
    forms['addTeamForm'] = AddTeamForm(request.form, csrf_enabled=False)
    
    choices = [(team['team_id'], team['team_name']) for team in execute_db_query('select team_id, team_name from team')]
    forms['addDNSServiceForm'] = AddDNSServiceForm(request.form, csrf_enabled=False)
    forms['addWebServiceForm'] = AddWebServiceForm(request.form, csrf_enabled=False)
    forms['addMailServiceForm'] = AddMailServiceForm(request.form, csrf_enabled=False)
    forms['addDNSServiceForm'].team_name.choices = choices
    forms['addWebServiceForm'].team_name.choices = choices
    forms['addMailServiceForm'].team_name.choices = choices
    return render_template('configure.html', forms=forms)

@app.route('/team/add', methods=['POST'])
def add_team():
    """
    The AddTeamForm posts to this page. Add a team to the database, and redirect back to the configure page.
    """
    form = AddTeamForm(request.form, csrf_enabled=False)
    if form.validate():
        execute_db_query('INSERT INTO team(team_name) VALUES(?)', [form.team_name.data])
    else:
        flash('Form not validated')
    return redirect(url_for('configure'))

@app.route('/team/remove', methods=['POST'])
def remove_team():
    """
    The RemoveTeamForm posts to this page. Remove a team from the database, and redirect back to the configure page.
    """
    team_id = request.form['team_id']
    execute_db_query('DELETE from team WHERE team_id = ?', [team_id])
    return redirect(url_for('configure'))

@app.route('/service/dns/add', methods=['POST'])
def add_dns_service():
    """
    The AddDNSServiceForm posts to this page. Add a DNS service to the database, and redirect back to the configure page.
    """
    form = AddDNSServiceForm(request.form, csrf_enabled=False)
    choices = [(team['team_id'], team['team_name']) for team in execute_db_query('select team_id, team_name from team')]
    form.team_name.choices = choices
    if form.validate():
        service_type_id = execute_db_query("select service_type_id from service_type where service_type_name = 'dns'")[0]['service_type_id']
        team_id = form.team_name.data
        execute_db_query('INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES(?, ?, ?, ?, ?, ?)', [service_type_id, team_id, form.service_name.data, form.service_connection.data, form.service_request.data, form.service_expected_result.data])
    else:
        flash('Form not validated')
    return redirect(url_for('configure'))

@app.route('/service/web/add', methods=['POST'])
def add_web_service():
    """
    The AddWebServiceForm posts to this page. Add a Web service to the database, and redirect back to the configure page.
    """
    form = AddWebServiceForm(request.form, csrf_enabled=False)
    choices = [(team['team_id'], team['team_name']) for team in execute_db_query('select team_id, team_name from team')]
    form.team_name.choices = choices
    if form.validate():
        team_id = form.team_name.data
        service_name = form.service_name.data
        
        service_url = urlparse(form.service_url.data)
        service_type_name = service_url.scheme
        service_connection = service_url.netloc

        filename = secure_filename(form.service_file.data.filename)
        form.service_file.data.save('data/uploads/' + filename)
        service_request = service_url.path
        service_expected_result = filename
        
        service_type_id = execute_db_query('select service_type_id from service_type where service_type_name = ?', [service_type_name])[0]['service_type_id']
        execute_db_query('INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES(?, ?, ?, ?, ?, ?)', [service_type_id, team_id, service_name, service_connection, service_request, service_expected_result])
    else:
        flash('Form not validated')
    return redirect(url_for('configure'))

@app.route('/service/mail/add', methods=['POST'])
def add_mail_service():
    """
    The AddMailServiceForm posts to this page. Add a mail service to the database, and redirect back to the configure page.
    """
    form = AddMailServiceForm(request.form, csrf_enabled=False)
    choices = [(team['team_id'], team['team_name']) for team in execute_db_query('select team_id, team_name from team')]
    form.team_name.choices = choices
    if form.validate():
        team_id = form.team_name.data
        service_name = form.service_name.data
        service_connection = form.service_connection.data
        service_request = form.from_email.data + ':' + form.to_email.data + ':' + form.service_expected_result.data
        service_expected_result = form.service_expected_result.data
        service_type_id = execute_db_query("select service_type_id from service_type where service_type_name = 'mail'")[0]['service_type_id']
        execute_db_query('INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES(?, ?, ?, ?, ?, ?)', [service_type_id, team_id, service_name, service_connection, service_request, service_expected_result])
    else:
        flash('Form not validated')
    return redirect(url_for('configure'))

@app.route('/service/remove', methods=['POST'])
def remove_service():
    """
    The RemoveServiceForm posts to this page. Removes a service from the database and redirects back to the configure page.
    """
    service_id = request.form['service_id']
    execute_db_query('DELETE from service where service_id = ?', [service_id])
    return redirect(url_for('configure'))

@app.route('/errors')
def errors():
    """
    The error page displays all current service errors
    """
    return render_template('errors.html')

@app.route('/scoreboard')
def scoreboard():
    """
    The scoreboard page displays a scoreboard of ranked teams, and detailed service scores.
    """
    return render_template('scoreboard.html')

@app.route('/')
def home():
    """
    Redirect the root path to the scoreboard.
    """
    return redirect(url_for('scoreboard'))

def poll():
    """
    Iterates over all the active services in the database and attempt to execute that service's functionality.
    The success or failure of the service and any error messages are stored in the database.
    """
    for service in execute_db_query('select * from service where service_active = 1'):
        row = execute_db_query('select * from service_type join service ON (service_type.service_type_id = service.service_type_id) where service.service_type_id = ?', [service['service_type_id']])[0]
        if row:
            id = service['service_id']
            type = row['service_type_name']
            server = service['service_connection']
            request = service['service_request']
            eresult = service['service_expected_result']
            match = False
            if type == 'dns':
                result = ''
                try:
                    resolv = dns.resolver.Resolver()
                    resolv.nameservers = [server]
                    resolv.timeout = 4
                    resolv.lifetime = 4
                    answers = resolv.query(request, 'A')
                    for rdata in answers:
                        result = rdata.to_text()
                except DNSException:
                    execute_db_query('insert into error(service_id, error_message) values(?,?)', [id, 'DNS Timeout on request for: ' + request + ' using server: ' + server])
                if result == eresult:
                    match = True
                else:
                    execute_db_query('insert into error(service_id,error_message) values(?,?)', [id, 'DNS Request result: ' + result + ' did not match expected: ' + eresult])

            elif type == 'http' or type == 'https':
                try:
                    result = requests.get(type + '://' + server + request, timeout=2, verify=False).text
                    if os.path.isfile(eresult):
                        upload = open(eresult, 'r')
                        eresult = upload.read()
                        upload.close()
                        # Only comparing first 10 lines for now. Have no good way to compare dynamic portions of a webpage.
                        one = eresult.splitlines(1)[0:10]
                        two = result.splitlines(1)[0:10]
                        if one == two:
                            match = True
                        else:
                            diff = difflib.unified_diff(one, two)
                            execute_db_query('insert into error(service_id,error_message) values(?,?)', [id, 'HTTP(S) Request result did not match expected. Diff: \n' + ''.join(diff)])
                    else:
                        execute_db_query('insert into error(service_id, error_message) values(?,?)', [id, 'Local filename for expected result: ' + eresult + ' does not exist.'])
                except requests.exceptions.RequestException as e:
                    execute_db_query('insert into error(service_id,error_message) values(?,?)', [id, 'HTTP(S) Request resulted in exception: ' + str(e)]) 
 
            elif type == 'ftp':
                ftp = FTP(server)
                ftp.login()
                resultStringIO = StringIO()
                ftp.retrbinary('RETR ' + request, resultStringIO.write)
                result = resultStringIO.getvalue()
                if os.path.isfile(eresult):
                    upload = open(eresult, 'r')
                    eresult = upload.read()
                    upload.close()
                    if result == eresult:
                        match = True
                    else:
                        diff = difflib.unified_diff(eresult, result)
                        execute_db_query('insert into error(service_id,error_message) values(?,?)', [id, 'FTP Request result did not match expected. Diff: \n' + ''.join(diff)])
                else:
                    execute_db_query('insert into error(service_id, error_message) values(?,?)', [id, 'Local filename for expected result: ' + eresult + ' does not exist.'])
            
            elif type == 'mail':
                sender = request.split(':')[0]
                recipient = request.split(':')[1]
                msg = request.split(':')[2]
                smtpFailure = False
                try:
                    smtpServer = smtplib.SMTP(server)
                    smtpServer.sendmail(sender,recipient,msg)
                    smtpServer.quit()
                except Exception as e:
                    execute_db_query('insert into error(service_id,error_message) values(?,?)', [id, 'SMTP Request resulted in exception: ' + str(e)])
                    smtpFailure = True
                if not smtpFailure:
                    try: 
                        Mailbox = poplib.POP3(server, timeout=15)
                        Mailbox.user(sender.split('@')[0])
                        Mailbox.pass_('ccdc')
                        numMessages = len(Mailbox.list()[1])
                        if numMessages < 1:
                            execute_db_query('insert into error(service_id,error_message) values(?,?)', [id, 'POP3 Request returned an empty mailbox. SMTP send or POP3 receive may have failed.'])
                        else:
                            # Retrieve only the latest message
                            message = Mailbox.retr(numMessages)[1]
                            result = message[-2]
                            if result == eresult:
                                match = True
                            else: 
                                diff = difflib.unified_diff(eresult, result)
                                execute_db_query('insert into error(service_id,error_message) values(?,?)', [id, 'POP3 response did not match expected result. Diff: \n' + ''.join(diff)])
                    except Exception as e:
                        execute_db_query('insert into error(service_id,error_message) values(?,?)', [id, 'POP3 Request resulted in exception: ' + str(e)])
                
            if match:
                execute_db_query('insert into poll(poll_score,service_id) values(1,?)', [id])
            else:
                execute_db_query('insert into poll(poll_score,service_id) values(0,?)', [id])

def poll_forever():
    """
    Poll all services every 5 seconds.
    """
    while True:
        try:
            sleep(5)
            poll()
        except Exception as e:
            print 'poll exception: ' + str(e)
            pass


if __name__ == "__main__":
    pollThread = Thread(target=poll_forever)
    pollThread.setDaemon(True)
    pollThread.start()
    app.run(host='0.0.0.0')

