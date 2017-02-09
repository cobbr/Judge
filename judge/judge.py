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
import tasks
import db

# Application settings
app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

@app.context_processor
def utility_processor():
    """
    Exports functions that can be used in Jinja templates.
    """
    return dict(execute_db_query=db.execute_db_query)

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
    db.database_populate()
    print 'Done.'

# WTF-Form classes
# Used to create functional forms for adding/removing services/teams within the Web UI

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

    choices = [(team['team_id'], team['team_name']) for team in db.execute_db_query('select team_id, team_name from team')]
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
    if app.config['ALLOW_CONFIG']:
        if form.validate():
            db.execute_db_query('INSERT INTO team(team_name) VALUES(?)', [form.team_name.data])
        else:
            flash('Form not validated')
    else:
        flash("Configuration is not allowed on this instance of Judge");
    return redirect(url_for('configure'))

@app.route('/team/remove', methods=['POST'])
def remove_team():
    """
    The RemoveTeamForm posts to this page. Remove a team from the database, and redirect back to the configure page.
    """
    team_id = request.form['team_id']
    if app.config['ALLOW_CONFIG']:
        db.execute_db_query('DELETE from team WHERE team_id = ?', [team_id])
    else:
        flash("Configuration is not allowed on this instance of Judge");
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
        flash("Configuration is not allowed on this instance of Judge");
    return redirect(url_for('configure'))

@app.route('/service/web/add', methods=['POST'])
def add_web_service():
    """
    The AddWebServiceForm posts to this page. Add a Web service to the database, and redirect back to the configure page.
    """
    form = AddWebServiceForm(request.form, csrf_enabled=False)
    if app.config['ALLOW_CONFIG']:
        choices = [(team['team_id'], team['team_name']) for team in db.execute_db_query('select team_id, team_name from team')]
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

            service_type_id = db.execute_db_query('select service_type_id from service_type where service_type_name = ?', [service_type_name])[0]['service_type_id']
            db.execute_db_query('INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES(?, ?, ?, ?, ?, ?)', [service_type_id, team_id, service_name, service_connection, service_request, service_expected_result])
        else:
            flash('Form not validated')
    else:
        flash("Configuration is not allowed on this instance of Judge");
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
            service_request = form.from_email.data + ':' + form.to_email.data + ':' + form.service_expected_result.data
            service_expected_result = form.service_expected_result.data
            service_type_id = db.execute_db_query("select service_type_id from service_type where service_type_name = 'mail'")[0]['service_type_id']
            db.execute_db_query('INSERT INTO service(service_type_id, team_id, service_name, service_connection, service_request, service_expected_result) VALUES(?, ?, ?, ?, ?, ?)', [service_type_id, team_id, service_name, service_connection, service_request, service_expected_result])
        else:
            flash('Form not validated')
    else:
        flash("Configuration is not allowed on this instance of Judge");
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
        flash("Configuration is not allowed on this instance of Judge");
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
