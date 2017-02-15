# Judge
#
# Debugging/Scoring utility for a CCDC team
#
# Author: Ryan Cobb

# import OS libraries
import os.path
from threading import Thread
from time import sleep

# import flask libraries
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, validators
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename
from werkzeug.datastructures import CombinedMultiDict

from urlparse import urlparse

import tasks
import db

# Application settings
app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
if os.path.isfile('instance/config.py'):
    app.config.from_pyfile('config.py')
app.config['UPLOAD_FOLDER'] = 'data/uploads'

@app.context_processor
def utility_processor():
    """
    Exports functions that can be used in Jinja templates.
    """
    return dict(execute_db_query=db.execute_db_query, allow_config=app.config['ALLOW_CONFIG'])

@app.cli.command('setup')
def setup():
    """
    Flask command line function that creates or clears the database.
    """
    if os.path.isfile('data/judge.db'):
        os.remove('data/judge.db')
    print 'Initializing database...'
    db.database_create()
    print 'Done.'

@app.cli.command('populate')
def populate():
    """
    Flask command line function that populates the database with default data
    """
    print 'Populating database...'
    db.database_populate(app.config['SERVICES_FILE'])
    print 'Done.'

# WTF-Form classes
# Used to create functional forms for adding/removing services/teams within the Web UI

class AddTeamForm(FlaskForm):
    team_name = StringField('Team Name', [validators.Length(min=1, max=50)], render_kw={"placeholder": "Team Name"})

class AddDNSServiceForm(FlaskForm):
    team_name = SelectField('Team', coerce=int)
    service_name = StringField('Service Name', [validators.Length(min=1, max=50)], render_kw={"placeholder": "Service Name"})
    service_connection = StringField('DNS Server IP', [validators.IPAddress()], render_kw={"placeholder": "IP Address"})
    service_request = StringField('DNS Lookup Hostname', [validators.Length(min=1, max=50)], render_kw={"placeholder": "Domain Name"})
    service_expected_result = StringField('Expected IP Result', [validators.IPAddress()], render_kw={"placeholder": "IP Address"})

class AddWebServiceForm(FlaskForm):
    team_name = SelectField('Team', coerce=int)
    service_name = StringField('Service Name', [validators.Length(min=1, max=50)], render_kw={"placeholder": "Service Name"})
    service_url = StringField('HTTP(S)/FTP URL', [validators.URL()], render_kw={"placeholder": "http://www.example.com"})
    # service_file = FileField('Expected File')

class AddMailServiceForm(FlaskForm):
    team_name = SelectField('Team', coerce=int)
    service_name = StringField('Service Name', [validators.Length(min=1, max=50)], render_kw={"placeholder": "Service Name"})
    service_connection = StringField('Mail Server IP', [validators.IPAddress()], render_kw={"placeholder": "IP Address"})
    from_email = StringField('From', [validators.Length(min=1, max=50)], render_kw={"placeholder": "Username:Password@example.com"})
    to_email = StringField('To', [validators.Length(min=1, max=50)], render_kw={"placeholder": "Username:Password@example.com"})
    service_expected_result = StringField('Message', [validators.Length(min=1,max=200)], render_kw={"placeholder": "Message Content"})

# Flask web routes
@app.route('/configure', methods=['GET'])
def configure():
    """
    The configure page is used to add/remove teams/services.
    """
    if app.config['ALLOW_CONFIG']:
        forms = {}
        forms['addTeamForm'] = AddTeamForm(request.form, csrf_enabled=False)

        choices = [(team['team_id'], team['team_name']) for team in db.execute_db_query('select team_id, team_name from team')]
        forms['addDNSServiceForm'] = AddDNSServiceForm(request.form, csrf_enabled=False)
        forms['addWebServiceForm'] = AddWebServiceForm(CombinedMultiDict((request.files, request.form)))
        forms['addMailServiceForm'] = AddMailServiceForm(request.form, csrf_enabled=False)
        forms['addWebServiceForm'].team_name.choices = choices
        forms['addDNSServiceForm'].team_name.choices = choices
        forms['addMailServiceForm'].team_name.choices = choices
        return render_template('configure.html', forms=forms, active_page='configure')
    else:
        return redirect(url_for('scoreboard'))

@app.route('/team/add', methods=['POST'])
def add_team():
    """
    The AddTeamForm posts to this page. Add a team to the database, and redirect back to the configure page.
    """
    form = AddTeamForm(request.form, csrf_enabled=False)
    if app.config['ALLOW_CONFIG']:
        if form.validate():
            db.execute_db_query('INSERT INTO team(team_name) VALUES(?)', [form.team_name.data])
        else:
            flash('Form not validated')
    else:
        return redirect(url_for('scoreboard'))
    return redirect(url_for('configure'))

@app.route('/team/remove', methods=['POST'])
def remove_team():
    """
    The RemoveTeamForm posts to this page. Remove a team from the database, and redirect back to the configure page.
    """
    team_id = request.form['team_id']
    if app.config['ALLOW_CONFIG']:
        db.execute_db_query('DELETE from service where team_id = ?', [team_id])
        db.execute_db_query('DELETE from team WHERE team_id = ?', [team_id])
    else:
        return redirect(url_for('scoreboard'))
    return redirect(url_for('configure'))

@app.route('/service/dns/add', methods=['POST'])
def add_dns_service():
    """
    The AddDNSServiceForm posts to this page. Add a DNS service to the database, and redirect back to the configure page.
    """
    form = AddDNSServiceForm(request.form, csrf_enabled=False)
    if app.config['ALLOW_CONFIG']:
        choices = [(team['team_id'], team['team_name']) for team in db.execute_db_query('select team_id, team_name from team')]
        form.team_name.choices = choices
        if form.validate():
            service_type_id = db.execute_db_query("select service_type_id from service_type where service_type_name = 'dns'")[0]['service_type_id']
            team_id = form.team_name.data
            db.execute_db_query('INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES(?, ?, ?, ?, ?, ?)', [service_type_id, team_id, form.service_name.data, form.service_connection.data, form.service_request.data, form.service_expected_result.data])
        else:
            flash('Form not validated')
    else:
        return redirect(url_for('scoreboard'))
    return redirect(url_for('configure'))

# WTF-Form FileField not working, doing all validation manually for this route
@app.route('/service/web/add', methods=['POST'])
def add_web_service():
    """
    The AddWebServiceForm posts to this page. Add a Web service to the database, and redirect back to the configure page.
    """
    if app.config['ALLOW_CONFIG']:
        if 'file' not in request.files:
            return redirect('configure')
        file = request.files['file']
        if file.filename == '':
            return redirect('configure')
        team_id = request.form['team_name']
        team_choices = [str(team['team_id']) for team in db.execute_db_query('select team_id from team')]
        if not team_id in team_choices:
            return redirect('configure')
        service_name = request.form['service_name']
        service_url = urlparse(request.form['service_url'])
        service_type_name = service_url.scheme
        service_connection = service_url.netloc
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        service_request = service_url.path
        service_expected_result = filename
        service_type_id = db.execute_db_query('select service_type_id from service_type where service_type_name = ?', [service_type_name])[0]['service_type_id']
        db.execute_db_query('INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES(?, ?, ?, ?, ?, ?)', [service_type_id, team_id, service_name, service_connection, service_request, service_expected_result])
    else:
        return redirect(url_for('scoreboard'))
    return redirect(url_for('configure'))

@app.route('/service/mail/add', methods=['POST'])
def add_mail_service():
    """
    The AddMailServiceForm posts to this page. Add a mail service to the database, and redirect back to the configure page.
    """
    form = AddMailServiceForm(request.form, csrf_enabled=False)
    if app.config['ALLOW_CONFIG']:
        choices = [(team['team_id'], team['team_name']) for team in db.execute_db_query('select team_id, team_name from team')]
        form.team_name.choices = choices
        if form.validate():
            team_id = form.team_name.data
            service_name = form.service_name.data
            service_connection = form.service_connection.data
            service_request = form.from_email.data + ',' + form.to_email.data + ',' + form.service_expected_result.data
            service_expected_result = form.service_expected_result.data
            service_type_id = db.execute_db_query("select service_type_id from service_type where service_type_name = 'mail'")[0]['service_type_id']
            db.execute_db_query('INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES(?, ?, ?, ?, ?, ?)', [service_type_id, team_id, service_name, service_connection, service_request, service_expected_result])
        else:
            flash('Form not validated')
    else:
        return redirect(url_for('scoreboard'))
    return redirect(url_for('configure'))

@app.route('/service/remove', methods=['POST'])
def remove_service():
    """
    The RemoveServiceForm posts to this page. Removes a service from the database and redirects back to the configure page.
    """
    if app.config['ALLOW_CONFIG']:
        service_id = request.form['service_id']
        db.execute_db_query('DELETE from service where service_id = ?', [service_id])
    else:
        return redirect(url_for('scoreboard'))
    return redirect(url_for('configure'))

@app.route('/errors')
def errors():
    """
    The error page displays all current service errors
    """
    return render_template('errors.html', active_page='errors')

@app.route('/scoreboard')
def scoreboard():
    """
    The scoreboard page displays a scoreboard of ranked teams, and detailed service scores.
    """
    return render_template('scoreboard.html', active_page='scoreboard')

@app.route('/')
def home():
    """
    Redirect the root path to the scoreboard.
    """
    return redirect(url_for('scoreboard'))

def poll_forever():
    """
    Poll all services continuously
    """
    while True:
        try:
            sleep(app.config['POLL_TIMEOUT'])
            tasks.poll()
        except Exception as e:
            print 'poll exception: ' + repr(e)
            pass

def go():
    pollThread = Thread(target=poll_forever)
    pollThread.setDaemon(True)
    pollThread.start()
    app.run(host='0.0.0.0')
